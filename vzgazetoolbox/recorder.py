# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Gaze and object tracking and recording class

import time
import math
import copy 
import random 
import pickle

import viz
import vizact
import viztask
import vizshape

from .data import *
from .stats import *
from .eyeball import Eyeball

class VzGazeRecorder():
	
	def __init__(self, eyetracker, DEBUG=False, missing_val=-99999.0, cursor=False):
		""" Eye movement recording and accuracy/precision measurement class.

		Args:
			eyetracker: Vizard extension sensor object representing an eye tracker
			DEBUG (bool): if True, print debug output to console
			missing_val (float): Value to log for missing data
			cursor (bool): if True, show cursor at current 3d gaze position
		"""
		
		self._tracker = eyetracker
		self._tracker_type = type(eyetracker).__name__
		self.debug = DEBUG
		
		# Additional tracked Vizard nodes
		self._tracked_nodes = {}

		# Value for missing data, since we can't use np.nan
		self.MISSING = missing_val
	
		# Latest gaze data
		self._gazedir = [self.MISSING, self.MISSING, self.MISSING] 
		self._gaze3d = [self.MISSING, self.MISSING, self.MISSING]
		self._gaze3d_valid = False
		self._gaze3d_intersect = None
		self._gaze3d_last_valid = None

		# Sample recording
		self.recording = False
		self._force_update = False
		self._samples = []
		self._val_samples = []
		self._events = []
		self._recorder = vizact.onupdate(viz.PRIORITY_PLUGINS+1, self._onUpdate)
		
		# Gaze validation
		self._scene = viz.addScene()
		self.fix_size = 0.5 # radius in degrees
		
		# Gaze cursor
		self._cursor = vizshape.addSphere(radius=0.05, color=[1.0, 0.0, 0.0])
		self._cursor.disable(viz.INTERSECTION)
		self.showGazeCursor(cursor)
		
		
	def _dlog(self, text):
		""" Log debug information to console if debug output is enabled 
		
		Args:
			String to print
		"""
		if self.debug:
			print('[{:s}] {:.4f} - {:s}'.format('VZGAZE', viz.tick(), text))
			

	def _deg2m(self, x, d):
		""" Convert visual degrees to meters at given viewing distance
		
		Args:
			x (float): Value in visual degrees
			d (float): Viewing distance in meters
			
		Returns: value in meters
		"""
		m = d * math.tan(math.radians(x))
		return m


	def _get_val_samples(self):
		""" Retrieve and clear current validation data """
		s = self._val_samples
		self._val_samples = []
		return s
		
	
	def addTrackedNode(self, node, label):
		""" Specify a Vizard.Node3d whose position and orientation should be
		logged alongside gaze data. Ensure the node is not deleted after
		adding it to the recorder object!

		Args:
			node: any Vizard Node3D object
			label (str): Label for this node in log files
		"""
		reserved = ['view', 'tracker', 'gaze', 'gaze3d', 'pupil'] + self._tracked_nodes.keys()
		if label.lower() in reserved:
			raise ValueError('Label "{:s}" already exists! Please choose a different label.'.format(label))
		self._tracked_nodes[label] = node
		self._dlog('Starting logging of node {:s} (ID: {:d}).'.format(label, node.id))


	def getCurrentGazePoint(self):
		""" Returns the current 3d gaze point if gaze intersects with the scene. """
		return self._gaze3d


	def getCurrentGazeMatrix(self):
		""" Returns the current gaze direction transform matrix """
		return self._gazedir


	def getCurrentGazeTarget(self):
		""" Returns the currently fixated node if a valid intersection is found """
		return self._gaze3d_intersect


	def getLastValidGazeTarget(self):
		""" Returns the node that last received a valid gaze intersection """
		return self._gaze3d_last_valid


	def showGazeCursor(self, visible):
		""" Set visibility of the gaze cursor node """
		self._cursor.visible(visible)


	def previewTargets(self, targets):
		""" Preview a set of validation targets without actually validating 
		
		Args:
			targets: One of the following:
				- Target set from vzgazetoolbox.VAL_TAR_*, OR
				- List of targets (x, y, depth), x/y in visual degrees, depth in m
		"""
		prev_scene = viz.MainWindow.getScene()
		viz.MainWindow.setScene(self._scene)

		tar_obj = []
		for tgt in targets:	
			t = vizshape.addSphere(radius=self._deg2m(self.fix_size, tgt[2]), scene=self._scene, color=[1.0, 1.0, 1.0])
			if tgt[0] == 0.0 and tgt[1] == 0.0:
				# Show central target in red for aligment
				t.color([1.0, 0.0, 0.0])
			t_link = viz.link(viz.MainView, t, enabled=True)
			t_link.preTrans([self._deg2m(tgt[0], tgt[2]), self._deg2m(tgt[1], tgt[2]), tgt[2]])
			tar_obj.append(t)
		
		self._dlog('Previewing set of {:d} targets.'.format(len(targets)))
		yield viztask.waitKeyDown(' ')
		
		for t in tar_obj:
			t.remove()
		viz.MainWindow.setScene(prev_scene)
		self._dlog('Original scene returned')


	def validate(self, targets=None, dur=2000, tar_color=[1.0, 1.0, 1.0], randomize=True):
		""" Measure gaze accuracy and precision for a set of head-locked targets
		in a special validation scene. 
		
		Args:
			targets: One of the following:
				- Target set from vzgazetoolbox.VAL_TAR_*, OR
				- List of targets (x, y, depth), x/y in visual degrees, depth in m
			dur (int): sampling duration per target, in ms
			tar_color (3-tuple): Target sphere color
			randomize (bool): if True, randomize target order in each validation
		
		Returns: vzgazetoolbox.ValidationResult object 
		"""
		if targets is None:
			# Central target drift check (default)
			targets = VAL_TAR_C

		tar_obj = []
		
		# Set up targets and switch to validation scene
		for tgt in targets:		
			t = vizshape.addSphere(radius=self._deg2m(self.fix_size, tgt[2]), scene=self._scene, color=tar_color)
			t.visible(viz.OFF)
			t_link = viz.link(viz.MainView, t, enabled=True)
			t_link.preTrans([self._deg2m(tgt[0], tgt[2]), self._deg2m(tgt[1], tgt[2]), tgt[2]])
			tar_obj.append(t)

		prev_scene = viz.MainWindow.getScene()
		viz.MainWindow.setScene(self._scene)
		self._dlog('Validation scene set up complete')
		
		# Initialize validation recorder
		val_recorder = vizact.onupdate(-1, self.recordSample, is_val=True)
		val_recorder.setEnabled(False)
		self._val_samples = [] # task starts out enabled, so might have recorded a stray sample
		
		# Sample gaze data for each target
		if randomize:
			cal_targets = random.sample(zip(range(0, len(targets)), targets, tar_obj), len(targets))
		else:
			cal_targets = zip(range(0, len(targets)), targets, tar_obj)

		tar_data = []
		sam_data = []
		for (c, tarpos, ct) in cal_targets:

			d = {}

			yield viztask.waitTime(1.0)
			val_recorder.setEnabled(True)
			if self.recording:
				self.recordEvent('VAL_START {:d} {:.1f} {:.1f} {:.1f}'.format(c, *tarpos))
			ct.color(tar_color)
			ct.visible(viz.ON)
			
			yield viztask.waitTime(float(dur) / 1000)
			val_recorder.setEnabled(False)
			s = self._get_val_samples()
			ct.color([0.1, 1.0, 0.1])
			yield viztask.waitTime(0.2)
			
			ct.visible(viz.OFF)
			if self.recording:
				self.recordEvent('VAL_END {:d} {:.1f} {:.1f} {:.1f}'.format(c, *tarpos))
			
			delta = []
			deltaX = []
			deltaY = []
			gazeX = []
			gazeY = []
			
			d['set_no'] = c
			d['x'] =  tarpos[0]
			d['y'] =  tarpos[1]
			d['d'] =  tarpos[2]

			for sam in s[20:]:
				# gaze-in-headset Euler angles
				# Note: pitch angle (gazeTdir[1]) is positive-down, thus it is flipped here
				gazeTdir = [sam['tracker_dirX'], -sam['tracker_dirY'], sam['tracker_dirZ']]
				gazeX.append(gazeTdir[0])
				gazeY.append(gazeTdir[1])

				dX = gazeTdir[0] - tarpos[0]
				dY = gazeTdir[1] - tarpos[1]
				dAbs = math.hypot(dX, dY)
				delta.append(dAbs)
				deltaX.append(dX)
				deltaY.append(dY)

			# TODO: print validation results onto console and event log
			# TODO: restrict samples used for averaging to last n samples
			
			# Gaze position and offset
			d['avgX'] = mean(gazeX)
			d['avgY'] = mean(gazeY)
			d['medX'] = median(gazeX)
			d['medY'] = median(gazeY)
			d['offX'] = mean(deltaX)
			d['offY'] = mean(deltaY)

			# Accuracy 
			d['acc'] = mean(delta)
			d['accX'] = mean([abs(v) for v in deltaX])
			d['accY'] = mean([abs(v) for v in deltaY])
			d['medacc'] = median(delta)
			d['medaccX'] = median([abs(v) for v in deltaX])
			d['medaccY'] = median([abs(v) for v in deltaY])
			
			# Precision
			d['sd'] = sd(delta)
			d['sdX'] = sd(deltaX)
			d['sdY'] = sd(deltaY)
			d['rmsi'] = rmsi(delta)
			d['rmsiX'] = rmsi(deltaX)
			d['rmsiY'] = rmsi(deltaY)

			tar_data.append(d)
			sam_data.append(s)

			self._dlog('VAL_END {:d} {:.1f} {:.1f} {:.1f}'.format(c, *tarpos))

		# Remove validation recorder
		val_recorder.setEnabled(False)
		val_recorder.remove()

		# Calculate grand average for each measure
		avg_data = {}
		for tar in tar_data:
			for var in tar.keys():
				if var not in avg_data:
					avg_data[var] = []
				avg_data[var].append(tar[var])
		for var in avg_data.keys():
			avg_data[var] = mean(avg_data[var])

		# Return to previous scene
		for t in tar_obj:
			t.remove()
		viz.MainWindow.setScene(prev_scene)
		self._dlog('Original scene returned')
		
		rv = ValidationResult(label='validation', time=time.strftime('%d.%m.%Y %H:%M:%S', time.localtime()),
							  result=avg_data, samples=sam_data, targets=tar_data)
		viztask.returnValue(rv)


	def _onUpdate(self, is_val=False):
		""" Task callback that runs on each display frame. Always updates 
		current gaze data properties, triggers sample recording if recording is on.
	
		Args:
			is_val (bool): if True, record to validation dataset (internal use)
		"""
		if self._force_update:
			viz.update(viz.UPDATE_PLUGINS | viz.UPDATE_LINKS)

		time_ms = viz.tick() * 1000.0		# Vizard time
		frame = viz.getFrameNumber()		# Vizard frame number
		clock = time.clock() * 1000.0 		# Python system time

		# Gaze and view nodes
		gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
		cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
		gW = copy.deepcopy(gT)				# Gaze-in-World FoR
		gW.postMult(cW)
		self._gazedir = gW
		nodes = {'tracker': gT,
				 'view':	cW,
				 'gaze': 	gW}

		# Additional tracked nodes
		for obj in self._tracked_nodes.keys():
			nodes[obj] = self._tracked_nodes[obj].getMatrix()

		# Update current gaze information and cursor position
		g3D_line = gW.getLineForward(1000)
		g3D_test = viz.intersect(g3D_line.begin, g3D_line.end)
		if g3D_test.valid:
			self._gaze3d = g3D_test.point
			self._gaze3d_valid = True
			self._gaze3d_intersect = g3D_test.object
			self._gaze3d_last_valid = g3D_test.object
			self._cursor.setPosition(g3D_test.point)
		else:
			self._gaze3d = [self.MISSING, self.MISSING, self.MISSING]
			self._gaze3d_valid = False
			self._gaze3d_intersect = None

		# Record sample if enabled
		if self.recording:
			sample = ((time_ms, frame, clock), nodes)
			self.recordSample(is_val=is_val, sample=sample)


	def recordSample(self, console=False, is_val=False, sample=None):
		""" Records transform matrices for head, gaze and tracked objects for the
		current sample. Can also be called manually to record a single frame.
		
		Args:
			console (bool): if True, print logged value to Vizard console
			is_val (bool): if True, record to validation dataset (internal use)
			sample: sample data, if called via _onUpdate (internal use)
		"""
		s = {}

		if sample is not None:
			# Store sample data coming from update callback
			(timing, nodes) = sample
			s['time'] = timing[0]
			s['frameno'] = timing[1]
			s['systime'] = timing[2]

		else:
			# Record a sample manually 
			s['time'] = viz.tick() * 1000.0
			s['frameno'] = viz.getFrameNumber()
			s['systime'] = time.clock() * 1000.0

			gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
			cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
			gW = copy.deepcopy(gT)				# Gaze-in-World FoR
			gW.postMult(cW)
			nodes = {'tracker': gT,	
					 'view':	cW,
					 'gaze': 	gW}

			for obj in self._tracked_nodes.keys():
				nodes[obj] = self._tracked_nodes[obj].getMatrix()

		# Store position and orientation data
		for lbl, node_matrix in nodes.iteritems():
			p = node_matrix.getPosition()
			d = node_matrix.getEuler()
			q = node_matrix.getQuat()
			s['{:s}_posX'.format(lbl)] = p[0]
			s['{:s}_posY'.format(lbl)] = p[1]
			s['{:s}_posZ'.format(lbl)] = p[2]
			s['{:s}_dirX'.format(lbl)] = d[0]
			s['{:s}_dirY'.format(lbl)] = d[1]
			s['{:s}_dirZ'.format(lbl)] = d[2]
			s['{:s}_quatX'.format(lbl)] = q[0]
			s['{:s}_quatY'.format(lbl)] = q[1]
			s['{:s}_quatZ'.format(lbl)] = q[2]
			s['{:s}_quatW'.format(lbl)] = q[3]

		# Store 3D gaze point data
		s['gaze3d_posX'] = self._gaze3d[0]
		s['gaze3d_posY'] = self._gaze3d[0]
		s['gaze3d_posZ'] = self._gaze3d[0]
		if self._gaze3d_valid:
			s['gaze3d_valid'] = 1
			s['gaze3d_object'] = str(self._gaze3d_intersect)
		else:
			s['gaze3d_valid'] = 0
			s['gaze3d_object'] = ''

		# Pupil size measurement (tracker-specific)
		pupilDia = self.MISSING
		if self._tracker_type == 'ViveProEyeTracker':
			pupilDia = self._tracker.getPupilDiameter()
			s['pupil_size'] = pupilDia

		if is_val:
			self._val_samples.append(s)
		else:
			self._samples.append(s)
		
		if console:
			# Note: printing coordinates will likely slow down rendering! Use for debugging only.
			cWp = cW.getPosition()
			cWd = cW.getEuler()
			gWp = gW.getPosition()
			gWd = gW.getEuler()
			outformat = '{:.4f} {:d}\tviewPOS=({:.3f}, {:.3f}, {:.3f}),\tviewDIR=({:.3f}, {:.3f}, {:.3f}),\tgazePOS=({:.3f}, {:.3f}, {:.3f}),\tgazeDIR=({:.3f}, {:.3f}, {:.3f}), p={:.3f}'
			print(outformat.format(cWp[0], cWp[1], cWp[2], cWd[0], cWd[1], cWd[2], gWp[0], gWp[1], gWp[2], gWd[0], gWd[1], gWd[2], pupilDia))


	def recordEvent(self, event=''):
		""" Record a time-stamped event string.
		This always works regardless of sample recording status.
		
		Args:
			event (str): event string to log
		"""
		ev = {'time': viz.tick() * 1000,
		 	  'message': str(event)}
		self._events.append(ev)


	def startRecording(self, force_update=False):
		""" Start recording of gaze samples and events 
		
		Args:
			force_update (bool): it True, force Vizard to update sensor data
		"""
		if not self.recording:
			self._force_update = force_update
			self.recording = True
			self.recordEvent('REC_START')
			if force_update:
				self._dlog('Recording started (forcing Vizard updates is on!)')
			else:
				self._dlog('Recording started.')
		
		
	def stopRecording(self):
		""" Stop recording of gaze samples and events """
		if self.recording:
			self.recording = False
			self.recordEvent('REC_STOP')
			self._dlog('Recording stopped.')
			self._force_update = False
		

	def saveRecording(self, sample_file=None, event_file=None, clear=True, sep='\t', quat=False):
		""" Save current gaze recording to a tab-separated CSV file 
		and clear the current recording by default.
		
		Args:
			sample_file: Name of output file to write gaze samples to
			event_file: Name of output file to write event data to
			clear (bool): if True, clear current recording after saving
			sep (str): Field separator in output file
			quat (bool): if True, also export rotation Quaternions
		"""
		# Samples: select keys to be exported and build file format
		fields = ['time', 'systime', 'view_posX', 'view_posY', 'view_posZ', 'view_dirX', 'view_dirY', 'view_dirZ',
				  'gaze_posX', 'gaze_posY', 'gaze_posZ', 'gaze_dirX', 'gaze_dirY', 'gaze_dirZ',
				  'gaze3d_valid', 'gaze3d_posX', 'gaze3d_posY', 'gaze3d_posZ', 'gaze3d_object']
		fmt = ['{:.4f}', '{:.4f}'] + ['{:.5f}',] * 12 + ['{:d}',] + ['{:.5f}',] * 3 + ['"{:s}"',]

		if 'pupil_size' in self._samples[0].keys():
			fields += ['pupil_size',]
			fmt += ['{:.5f}',]
		for lbl in self._tracked_nodes.keys():
			fields += ['{:s}_posX'.format(lbl), '{:s}_posY'.format(lbl), '{:s}_posZ'.format(lbl), 
					   '{:s}_dirX'.format(lbl), '{:s}_dirY'.format(lbl), '{:s}_dirZ'.format(lbl)]
			fmt += ['{:.5f}',] * 6
		if quat:
			fields += ['view_quatX', 'view_quatY', 'view_quatZ', 'view_quatW',
					   'gaze_quatX', 'gaze_quatY', 'gaze_quatZ', 'gaze_quatW']
			fmt += ['{:.5f}',] * 8
			for lbl in self._tracked_nodes.keys():
				fields += ['{:s}_quatX'.format(lbl), '{:s}_quatY'.format(lbl), '{:s}_quatZ'.format(lbl), '{:s}_quatW'.format(lbl)]
				fmt += ['{:.5f}',] * 4

		HEADER = sep.join(fields) + '\n'
		ROWFMT = sep.join(fmt) + '\n'
		
		# Events: build header
		evfields = ['time', 'message']
		EHEADER = sep.join(evfields) + '\n'
		EROWFMT = sep.join(['{:.4f}', '"{:s}"']) + '\n'
		
		if sample_file is not None:
			n = 0
			with open(sample_file, 'w') as of:
				of.write(HEADER)
				for sample in self._samples:
					row = [sample[f] for f in fields]
					of.write(ROWFMT.format(*row))
					n += 1
			self._dlog('Saved {:d} samples to file: {:s}'.format(n, sample_file))
		
		if event_file is not None:
			n = 0
			with open(event_file, 'w') as ef:
				ef.write(EHEADER)
				for event in self._events:
					ev = [event[f] for f in evfields]
					ef.write(EROWFMT.format(*ev))
					n += 1
			self._dlog('Saved {:d} events to file: {:s}'.format(n, event_file))

		if sample_file is None and event_file is None:
			self._dlog('Neither sample_file or event_file were specified. No data saved.')
		else:
			if clear:
				self._samples = []
				self._events = []
				self._dlog('Cleared sample and event recording. Pass clear=False to keep.')


	def clearRecording(self):
		""" Stops recording and clears both samples and events """
		self.recording = False
		self._samples = []
		self._events = []
		self._dlog('Cleared sample and event recording.')
