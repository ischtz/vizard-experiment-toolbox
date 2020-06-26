import copy
import math
import random

import viz
import vizact
import viztask
import vizshape
import vizmat
import vizinfo

# Default validation target coordinates

# single central target (default)
VAL_TAR_C =    [[0.0,  0.0,  6.0]]	

# 5-point cross at +/- 5 deg, 6m distance
VAL_TAR_CR5 =  [[0.0,  0.0,  6.0],	
				[5.0,  0.0,  6.0],
				[0.0,  -5.0, 6.0],
				[-5.0, 0.0,  6.0],
				[0.0, 5.0,   6.0]] # N=5

# 3x3 full square at +/- 5 deg, 6m distance
VAL_TAR_SQ5 =  [[0.0,  0.0,  6.0],
				[5.0,  0.0,  6.0],
				[0.0,  -5.0, 6.0],
				[-5.0, 0.0,  6.0],
				[0.0, 5.0,   6.0],
				[5.0, 5.0,   6.0],
				[5.0,  -5.0, 6.0],
				[-5.0, -5.0, 6.0],
				[-5.0,  5.0, 6.0]] # N=9

# 5x5 major positions, +/- 10 deg, 6m distance
VAL_TAR_CR10 = [[0.0,  0.0,  6.0],	
				[5.0,  0.0,  6.0],
				[0.0,  -5.0, 6.0],
				[-5.0, 0.0,  6.0],
				[0.0,  5.0,  6.0],
				[5.0,  5.0,  6.0],
				[5.0,  -5.0, 6.0],
				[-5.0, -5.0, 6.0],
				[-5.0,  5.0, 6.0],
				[10.0, 0.0,  6.0],
				[0.0, -10.0, 6.0],
				[-10.0, 0.0, 6.0],
				[0.0,  10.0, 6.0],
				[10.0, 10.0, 6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0]] # N=17

# 5x5 full square, +/- 10 deg, 6m distance
VAL_TAR_SQ10 = [[0.0,  0.0,   6.0],	
				[5.0,  0.0,   6.0],
				[0.0,  -5.0,  6.0],
				[-5.0, 0.0,   6.0],
				[0.0,  5.0,   6.0],
				[5.0,  5.0,   6.0],
				[5.0,  -5.0,  6.0],
				[-5.0, -5.0,  6.0],
				[-5.0,  5.0,  6.0],
				[10.0, 0.0,   6.0],
				[0.0, -10.0,  6.0],
				[-10.0, 0.0,  6.0],
				[0.0,  10.0,  6.0],
				[10.0, 10.0,  6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0],
				[10.0, 5.0,   6.0],
				[10.0, -5.0,  6.0],
				[5.0, -10.0,  6.0],
				[-5.0, -10.0, 6.0],				
				[-10.0, -5.0, 6.0],
				[-10.0, 5.0,  6.0],
				[-5.0, 10.0,  6.0], 
				[5.0, 10.0,   6.0]] # N=25

# 7x7 major positions, +/- 15 deg, 6m distance
VAL_TAR_CR15 = [[0.0,  0.0,   6.0],
				[5.0,  0.0,   6.0],
				[0.0,  -5.0,  6.0],
				[-5.0, 0.0,   6.0],
				[0.0,  5.0,   6.0],
				[5.0,  5.0,   6.0],
				[5.0,  -5.0,  6.0],
				[-5.0, -5.0,  6.0],
				[-5.0,  5.0,  6.0],
				[10.0, 0.0,   6.0],
				[0.0, -10.0,  6.0],
				[-10.0, 0.0,  6.0],
				[0.0,  10.0,  6.0],
				[10.0, 10.0,  6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0],
				[15.0, 0.0,   6.0],
				[0.0, -15.0,  6.0],
				[-15.0, 0.0,  6.0],
				[0.0, 15.0,   6.0],
				[15.0, 15.0,  6.0],
				[15.0, -15.0, 6.0],
				[-15.0,-15.0, 6.0],
				[-15.0, 15.0, 6.0]] # N=25
				
# 7x7 full square, +/- 15 deg, 6m distance
VAL_TAR_SQ15 = [[0.0,  0.0,   6.0],
				[5.0,  0.0,   6.0],
				[0.0,  -5.0,  6.0],
				[-5.0, 0.0,   6.0],
				[0.0,  5.0,   6.0],
				[5.0,  5.0,   6.0],
				[5.0,  -5.0,  6.0],
				[-5.0, -5.0,  6.0],
				[-5.0,  5.0,  6.0],
				[10.0, 0.0,   6.0],
				[0.0, -10.0,  6.0],
				[-10.0, 0.0,  6.0],
				[0.0,  10.0,  6.0],
				[10.0, 10.0,  6.0],
				[10.0, -10.0, 6.0],
				[-10.0,-10.0, 6.0],
				[-10.0, 10.0, 6.0],
				[10.0, 5.0,   6.0],
				[10.0, -5.0,  6.0],
				[5.0, -10.0,  6.0],
				[-5.0, -10.0, 6.0],
				[-10.0, -5.0, 6.0],
				[-10.0, 5.0,  6.0],
				[-5.0, 10.0,  6.0], 
				[5.0, 10.0,   6.0],
				[15.0, 0.0,   6.0],
				[0.0, -15.0,  6.0],
				[-15.0, 0.0,  6.0],
				[0.0, 15.0,   6.0],
				[15.0, 15.0,  6.0],
				[15.0, -15.0, 6.0],
				[-15.0,-15.0, 6.0],
				[-15.0, 15.0, 6.0],
				[15.0, 10.0,  6.0],
				[15.0, 5.0,   6.0],
				[15.0, -5.0,  6.0],
				[15.0, -10.0, 6.0],
				[10.0, -15.0, 6.0],
				[5.0, -15.0,  6.0],
				[-5.0, -15.0, 6.0],
				[-10.0,-15.0, 6.0],
				[-15.0,-10.0, 6.0],
				[-15.0, -5.0, 6.0],
				[-15.0, 5.0,  6.0],
				[-15.0, 10.0, 6.0],
				[-10.0, 15.0, 6.0],
				[-5.0, 15.0,  6.0],
				[5.0, 15.0,   6.0],
				[10.0, 15.0,  6.0]] # N=49


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
		self._gaze3d_intersect = None
		self._gaze3d_last_valid = None

		# Sample recording
		self.recording = False
		self._samples = []
		self._val_samples = []
		self._events = []
		self._recorder = vizact.onupdate(viz.PRIORITY_LINKS+1, self._onUpdate)
		
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


	def getCurrentGaze(self):
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

		
		
		
	def _onUpdate(self, console=False, is_val=False):
		""" Task callback that runs on each display frame. Always updates 
		current gaze data properties, triggers sample recording if recording is on.
	
		Args:
			console (bool): if True, print logged value to Vizard console
			is_val (bool): if True, record to validation dataset (internal use)
		"""
		# Update gaze direction transform
		gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
		cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
		gW = copy.deepcopy(gT)				# Gaze-in-World FoR
		gW.postMult(cW)
		self._gazedir = gW

		# Find 3D gaze point and target through ray intersection
		g3D_line = gW.getLineForward(1000)
		g3D_test = viz.intersect(g3D_line.begin, g3D_line.end)
		if g3D_test.valid:
			self._gaze3d = g3D_test.point
			self._gaze3d_intersect = g3D_test.object
			self._gaze3d_last_valid = g3D_test.object
			self._cursor.setPosition(g3D_test.point)
		else:
			self._gaze3d = [self.MISSING, self.MISSING, self.MISSING]
			self._gaze3d_intersect = None

		# Record sample if recording is enabled
		if self.recording:
			self.recordSample()


	def recordSample(self, console=False, is_val=False):
		""" Record transform matrices for head, gaze and tracked objects
		for the current sample. Can be called manually or in vizact.onupdate().
		
		Args:
			console (bool): if True, print logged value to Vizard console
			is_val (bool): if True, record to validation dataset (internal use)
		"""
		s = {}

		# Timing
		s['time'] = viz.tick() * 1000
		s['frameno'] = viz.getFrameNumber()

		# Collect transforms of built-in tracked nodes
		gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
		cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
		gW = copy.deepcopy(gT)				# Gaze-in-World FoR
		gW.postMult(cW)
		nodes = {'tracker': gT,	
				 'view':	cW,
				 'gaze': 	gW}

		# Add other (optional) tracked nodes
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

		# Find 3D gaze point through ray intersection method
		g3D = [self.MISSING, self.MISSING, self.MISSING]
		g3D_line = gW.getLineForward(1000)
		g3D_test = viz.intersect(g3D_line.begin, g3D_line.end)
		s['gaze3d_valid'] = 0
		s['gaze3d_object'] = ''
		if g3D_test.valid:
			g3D = g3D_test.point
			s['gaze3d_valid'] = 1
			s['gaze3d_object'] = str(g3D_test.name)
		s['gaze3d_posX'] = g3D[0]
		s['gaze3d_posY'] = g3D[1]
		s['gaze3d_posZ'] = g3D[2]

		# Pupil size measurement is tracker-specific
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


	def startRecording(self):
		""" Start recording of gaze samples and events """
		if not self.recording:
			self.recording = True
			self.recordEvent('REC_START')
			self._dlog('Recording started.')
		
		
	def stopRecording(self):
		""" Stop recording of gaze samples and events """
		if self.recording:
			self.recording = False
			self.recordEvent('REC_STOP')
			self._dlog('Recording stopped.')
		

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
		fields = ['time', 'view_posX', 'view_posY', 'view_posZ', 'view_dirX', 'view_dirY', 'view_dirZ',
				  'gaze_posX', 'gaze_posY', 'gaze_posZ', 'gaze_dirX', 'gaze_dirY', 'gaze_dirZ',
				  'gaze3d_valid', 'gaze3d_posX', 'gaze3d_posY', 'gaze3d_posZ', 'gaze3d_object']
		fmt = ['{:.4f}'] + ['{:.5f}',] * 12 + ['{:d}',] + ['{:.5f}',] * 3 + ['"{:s}"',]

		if 'pupil_size' in self._samples[0].keys():
			fields += 'pupil_size'
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



class VzGazePlayer():
	
	def __init__(self, recording=None, ui=True, show_eye=True, show_gaze=False):
		""" Eye movement replay class 
		
		Args:
			recording: file name of a CSV recording file to load, OR
				VzGazeRecorder instance to get sample data from
			ui (bool): if True, show Vizard UI panel with recording status
			show_eye (bool): if True, show Eyeball shape, else coordinate axes
			show_gaze (bool): if True, plot a sphere at the recorded 3d gaze point

		"""
		# Visualization objects
		self.gaze = vizshape.addSphere(radius=0.01, color=[1.0, 0.0, 0.0])
		self.showGazeCursor(show_gaze)
		if show_eye:
			self.eye = Eyeball(visible=False, pointer=True)
		else:
			self.eye = vizshape.addAxes(scale=[0.2, 0.2, 0.2])
		
		self._frame = 0
		self._samples = []
		self._player = None
		self.replaying = False
		self.finished = False

		# Load recording if specified
		if recording is not None:
			if type(recording) == 'str':
				self.loadRecording(recording)
			else:
				self._samples = recording._samples

		# Set up status GUI if enabled
		self._ui = None
		if ui:
			self._ui = vizinfo.InfoPanel('Gaze Data Replay', align=viz.ALIGN_RIGHT_TOP)
			self._ui_bar = self._ui.addItem(viz.addProgressBar('0/0'))
			self._set_ui()


	def _set_ui(self):
		""" Set GUI elements to display status (if enabled) """
		if self._ui is not None:
			if len(self._samples) == 0:
				self._ui_bar.message('No data')
			else:
				self._ui_bar.set(float(self._frame)/float(len(self._samples)))
				self._ui_bar.message('{:d}/{:d}'.format(self._frame, len(self._samples)))


	def loadRecording(self, sample_file, sep='\t'):
		""" Load a VzGazeRecorder samples file for replay
		
		Args:
			sample_file (str): Filename of CSV file to load
			sep (str): Field separator in CSV input file
		"""
		s = []
		with open(sample_file, 'r') as sf:
			lidx = 0
			for line in sf.readlines():
				if lidx == 0:
					lidx += 1
					continue # Skip header
					
				s.append([float(x) for x in line.split(sep)])
				lidx +=1 
			
		self._samples = s
		self._set_ui()
		print('Loaded {:d} replay samples from "{:s}".'.format(lidx, sample_file))
		

	def startReplay(self, from_start=True):
		""" Play the current recording frame by frame 
		
		Args:
			from_start (bool): if True, start replay from first frame 
		"""
		if from_start or self._frame >= len(self._samples):
			self._frame = 0
		if self._player is None:
			self._player = vizact.onupdate(0, self.replayCurrentFrame)
		if not self.replaying:
			self._player.setEnabled(True)
			self.replaying = True
			self.finished = False
			self.eye.visible(True)
			print('Replay started.')

		
	def stopReplay(self):
		""" Stop an ongoing replay """
		if self.replaying:
			if self._player is not None:
				self._player.setEnabled(False)
			self.replaying = False
			self.eye.visible(False)
			print('Replay stopped at frame {:d}.'.format(self._frame))

		
	def replayCurrentFrame(self, advance=True):
		""" Replay task. Sets up gaze position for each upcoming frame 
		
		Args:
			advance (bool): if True, advance to next frame (default).
		"""
		f = self._samples[self._frame]

		eye_pos = f[14:17] # gaze-in-world eye position
		eye_dir = f[17:20] # gaze-in-world angles
		gaze3d = f[21:24]  # gaze-in-workld intersection point
		eye_mat = viz.Matrix()
		eye_mat.setEuler([eye_dir[0], eye_dir[1], eye_dir[2]])
		eye_mat.setScale(self.eye.getScale())
		eye_mat.setPosition(eye_pos)
		
		self.eye.setMatrix(eye_mat)
		self.gaze.setPosition(gaze3d)

		self._set_ui()
		if self._frame == 0 or self._frame == len(self._samples) or self._frame % 100 == 0:
			print('Replaying frame {:d}/{:d}, t={:.2f}'.format(self._frame, len(self._samples), f[0]))
		
		if advance:
			self._frame += 1
		if self._frame >= len(self._samples):
			# Reached last frame, stop replay and reset
			self.replaying = False
			self.finished = True
			if self._player is not None:
				self._player.setEnabled(False)
			print('Replay finished.')


	def replayDone(self):
		""" Return True if replay is finished,
			use as viztask.waitTrue(object.replayDone)
		"""
		return self.finished


	def showGazeCursor(self, visible):
		""" Set visibility of the gaze cursor object """
		self.gaze.visible(visible)



class Eyeball(viz.VizNode):
	""" Simple eyeball object to visually indicate gaze direction """
	
	def __init__(self, radius=0.024, eyecolor='blue', pointer=False, gaze_length=100, visible=True):
		""" Initialize a new Eyeball node
		
		Args:
			radius (float): Eyeball radius in m
			eyecolor (str, 3-tuple): Iris color for this eye (see setEyeColor)
			pointer (bool): if True, start out the gaze pointer visible
			gaze_length (float): length of gaze pointer in m
			visible (bool): if False, Eyeball node starts out invisible
		"""

		self.eyecolors = {'brown': [0.387, 0.305, 0.203],
						  'blue':  [0.179, 0.324, 0.433],
						  'green': [0.109, 0.469, 0.277],
						  'grey':  [0.285, 0.461, 0.395]}
		
		eye = viz.addChild('unit_eye.gltf')
		eye.visible(visible)
		viz.VizNode.__init__(self, eye.id)
		
		# Add gaze direction pointer (invisible by default)
		self.pointer = vizshape.addCylinder(height=gaze_length, radius=0.05, axis=vizshape.AXIS_Z, parent=eye)
		self.pointer.setPosition([0.0, 0.0, (gaze_length/2)-radius-0.005])
		if not pointer:
			self.pointer.visible(viz.OFF)

		# Set a specific eye color (e.g. for disambiguation)
		eye.setScale([radius/2,] * 3)
		self.setEyeColor(eyecolor)
		
		
	def setEyeColor(self, color):
		""" Set iris color of this eyeball object
		
		Args:
			color : RGB 3-tuple, or one of 'brown', 'blue', 'green', 'grey'
		"""
		if type(color) == str:
			ec = self.eyecolors[color]
		else:
			ec = color

		self.getChild('Iris').color(ec)
		self.pointer.color(ec)


	def setGazePointer(self, visible=True):
		""" Show or hide the gaze pointer on the eye's Z axis
		
		Args:
			visible (bool): if True, draw gaze direction pointer
		"""
		self.pointer.visible(visible)

def showVRText(msg, color=[1.0, 1.0, 1.0], distance=2.0, scale=0.05, duration=3.0):
	""" Display head-locked message in VR, e.g. for instructions.
	
	Args:
		msg (str): Message text
		color: RBG 3-tuple of color values
		distance (float): Z rendering distance from MainView
		scale (float): Text node scaling factor
		duration (float): Message display duration (seconds)
	"""
	# Create 3D text object
	text = viz.addText3D(msg, scale=[scale, scale, scale], color=color)
	text.resolution(1.0)
	text.setThickness(0.1)
	text.alignment(viz.ALIGN_CENTER)
	
	# Lock text to user viewpoint at fixed distance
	text_link = viz.link(viz.MainView, text, enabled=True)
	text_link.preTrans([0.0, 0.0, distance])
	
	# Fade text away after <duration> seconds
	fadeout = vizact.fadeTo(0, time=0.7)
	yield viztask.waitTime(duration)
	text.addAction(fadeout)
	yield viztask.waitActionEnd(text, fadeout)
	text.remove()


def waitVRText(msg, color=[1.0, 1.0, 1.0], distance=2.0, scale=0.05, keys=' '):
	""" Display head-locked message in VR and wait for key press.
	
	Args:
		msg (str): Message text
		color: RBG 3-tuple of color values
		distance (float): Z rendering distance from MainView
		scale (float): Text node scaling factor
		keys (str): Key code(s) to dismiss message (see viztask.waitKeyDown)
	
	Returns: Vizard keypress event
	"""
	# Create 3D text object
	text = viz.addText3D(msg, scale=[scale, scale, scale], color=color)
	text.resolution(1.0)
	text.setThickness(0.1)
	text.alignment(viz.ALIGN_CENTER)
	
	# Lock text to user viewpoint at fixed distance
	text_link = viz.link(viz.MainView, text, enabled=True)
	text_link.preTrans([0.0, 0.0, distance])
	
	event = yield viztask.waitKeyDown(keys)
	text.remove()
	viztask.returnValue(event)
