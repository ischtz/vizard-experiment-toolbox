# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Gaze and object tracking and recording class

import sys
import time
import math
import copy 
import random 
import pickle
from builtins import object

import viz
import vizact
import vizmat
import viztask
import vizshape

from .data import *
from .stats import *
from .eyeball import Eyeball

# Python version compatibility
if sys.version_info[0] == 3:
	from time import perf_counter
else:
	from time import clock as perf_counter	


class VzGazeRecorder(object):
	
	def __init__(self, eyetracker, DEBUG=False, missing_val=-99999.0, cursor=False,
				 key_calibrate='c', key_preview='p', key_validate='v', targets=VAL_TAR_CR10,
				 prealloc=324000):
		""" Eye movement recording and accuracy/precision measurement class.

		Args:
			eyetracker: Vizard extension sensor object representing an eye tracker
			DEBUG (bool): if True, print debug output to console and store extra fields
			missing_val (float): Value to log for missing data
			cursor (bool): if True, show cursor at current 3d gaze position
			key_calibrate (str): Vizard key code that should trigger eye tracker calibration
			key_preview (str): Vizard key code that should trigger target preview
			key_validate (str): Vizard key code that should trigger gaze validation
			targets: default validation target set to use (see validate())
			prealloc (int): number of samples to preallocate to avoid skipped frames due to 
				Python list extension. Default should be good for 60 min at 90 Hz. 
		"""
		# Eye tracker properties
		self._tracker = eyetracker
		self._tracker_has_eye_flag = False
		self._tracker_type = type(eyetracker).__name__
		if self._tracker_type in ['ViveProEyeTracker']:
			# Trackers supporting monocular data via the sensor flag parameter
			self._tracker_has_eye_flag = True
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
		self._samples = [None,] * prealloc
		self._samples_idx = 0
		self._prealloc = prealloc
		self._val_samples = []
		self._events = []
		self._recorder = vizact.onupdate(viz.PRIORITY_PLUGINS+1, self._onUpdate)
		
		# Gaze validation
		self._scene = viz.addScene()
		self.fix_size = 0.5 # radius in degrees
		self.tar_plane_color = [0.4, 0.4, 0.4]
		self._last_val_result = None
		self._default_targets = targets
		
		# Gaze cursor
		self._cursor = vizshape.addSphere(radius=0.05, color=[1.0, 0.0, 0.0])
		self._cursor.disable(viz.INTERSECTION)
		self.showGazeCursor(cursor)

		# Register task callbacks for interactive keys
		if key_calibrate is not None:
			self._cal_callback = vizact.onkeydown(key_calibrate, viztask.schedule, self.calibrate)
			self._dlog('Key callback registered: Calibration ({:s}).'.format(key_calibrate))
		if key_validate is not None:
			self._val_callback = vizact.onkeydown(key_validate, viztask.schedule, self.validate)
			self._dlog('Key callback registered: Validation ({:s}).'.format(key_validate))
		if key_preview is not None:
			self._prev_callback = vizact.onkeydown(key_preview, viztask.schedule, self.previewTargets)
			self._dlog('Key callback registered: Target preview ({:s}).'.format(key_preview))


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


	def _record_val_sample(self):
		""" Record a gaze sample during validation """
		
		if self._force_update:
			viz.update(viz.UPDATE_PLUGINS | viz.UPDATE_LINKS)

		s = {}
		s['time'] = viz.tick() * 1000.0
		s['frameno'] = viz.getFrameNumber()
		s['systime'] = perf_counter() * 1000.0

		# Gaze, target, and view nodes
		cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
		gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
		vgT = gT.getForward()				# Gaze-in-Tracker unit vector
		gW = copy.deepcopy(gT)				# Gaze-in-World FoR
		gW.postMult(cW)
		vgW = gW.getForward()				# Gaze-in-World unit vector
		nodes = {'tracker': gT,
				 'view':	cW,
				 'gaze': 	gW}
		vecs = {'gazeVec':    vgW,
				'trackVec': vgT}

		# Monocular data, if available
		if self._tracker_has_eye_flag:	
			gTL = self._tracker.getMatrix(flag=viz.LEFT_EYE)
			gTR = self._tracker.getMatrix(flag=viz.RIGHT_EYE)
			vgTL = gTL.getForward()
			vgTR = gTR.getForward()
			gWL = copy.deepcopy(gTL)
			gWR = copy.deepcopy(gTR)
			gWL.postMult(cW)
			gWR.postMult(cW)
			vgWL = gWL.getForward()
			vgWR = gWR.getForward()
			nodes['trackerL'] = gTL
			nodes['trackerR'] = gTR
			nodes['gazeL'] = gWL
			nodes['gazeR'] = gWR
			vecs['gazeVecL'] = vgWL
			vecs['gazeVecR'] = vgWR
			vecs['trackVecL'] = vgTL
			vecs['trackVecR'] = vgTR

		# Store position data
		for lbl, node_matrix in nodes.items():
			p = node_matrix.getPosition()
			s['{:s}_posX'.format(lbl)] = p[0]
			s['{:s}_posY'.format(lbl)] = p[1]
			s['{:s}_posZ'.format(lbl)] = p[2]

		# Store gaze unit direction vectors
		for lbl, vec in vecs.items():
			s['{:s}_X'.format(lbl)] = vec[0]
			s['{:s}_Y'.format(lbl)] = vec[1]
			s['{:s}_Z'.format(lbl)] = vec[2]
		
		self._val_samples.append(s)
 
	
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
		reserved = ['view', 'tracker', 'gaze', 'gaze3d', 'pupil'] + list(self._tracked_nodes.keys())
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


	def getLastValResult(self):
		""" Return a copy of the ValidationResult object resulting from the most
		recent gaze validation measurement. """
		return copy.deepcopy(self._last_val_result)


	def measureIPD(self, sample_dur=1000.0):
		""" Measure Inter-Pupillary Distance (IPD) of the HMD wearer
		
		Args:
			sample_dur (float): sampling duration in ms

		Returns:
			IPD as a single float value, in mm 
		"""
		if not self._tracker_has_eye_flag:
			err = 'measureIPD() requires monocular gaze data, which is not available for the current eye tracker ({:s})'
			raise NotImplementedError(err.format(self._tracker_type))

		# Sample gaze data using the validation recorder
		val_recorder = vizact.onupdate(-1, self._record_val_sample)
		self._val_samples = [] # task starts out enabled, so might have recorded a stray sample
		yield viztask.waitTime(float(sample_dur) / 1000)
		val_recorder.setEnabled(False)
		s = self._get_val_samples()
		val_recorder.setEnabled(False)
		val_recorder.remove()

		# Calculate average IPD
		ipdval = []
		for sam in s:
			dX = abs(sam['trackerR_posX'] - sam['trackerL_posX'])
			ipdval.append(dX)

		ipd = mean(ipdval) * 1000.0
		self._dlog('measureIPD(): Mean IPD is {:.1f} mm'.format(ipd))
		viztask.returnValue(ipd)


	def previewTargets(self, targets=VAL_TAR_SQ10, cursor=False):
		""" Preview a set of validation targets without actually validating. If
		targets are specified for multiple depth planes, cycle through planes by
		pressing space.
		
		Args:
			targets: One of the following:
				- Target set from vzgazetoolbox.VAL_TAR_*, OR
				- List of targets (x, y, depth), x/y in visual degrees, depth in m
			cursor (bool): if True, show gaze cursor during preview
		"""
		prev_scene = viz.MainWindow.getScene()
		viz.MainWindow.setScene(self._scene)
		root = viz.addGroup(scene=self._scene)

		if cursor:
			cursor_state = self._cursor.getVisible()
			self._cursor.addParent(viz.WORLD, scene=self._scene)
			self.showGazeCursor(True)

		# Set up depth planes and targets
		t_dists = []
		t_planes = {}
		t_objs = {}
		for tgt in targets:
			d = tgt[2]
			if d not in t_dists:
				t_dists.append(d)
				t_planes[d] = vizshape.addPlane(size=(1000.0, 1000.0), axis=vizshape.AXIS_Z, scene=self._scene,
													 flipFaces=True, color=self.tar_plane_color, parent=root)
				t_planes[d].setPosition([0.0, 0.0, d], mode=viz.REL_PARENT)
				t_objs[d] = []
			
			# Find target position on depth plane using raycasting
			tar_mat = vizmat.Transform()
			tar_mat.makeEuler([tgt[0], -tgt[1], 0.0])
			tar_dir = tar_mat.getLineForward(1000)
			info = self._scene.intersect(tar_dir.begin, tar_dir.end, ignoreBackFace = False, all=True)
			tar_pos = None
			for obj in info:
				# Only intersect the correct plane
				if obj.object == t_planes[d]:
					tar_pos = obj.point
			t = viz.addGroup(scene=self._scene, parent=root)
			t_out = vizshape.addCylinder(radius=self._deg2m(self.fix_size, d), height=self._deg2m(self.fix_size/20.0, d), parent=t, scene=self._scene, axis=vizshape.AXIS_Z, color=(1, 1, 1))
			t_in = vizshape.addSphere(radius=self._deg2m(self.fix_size/5.0, d), parent=t, scene=self._scene, color=(0,0,0))
			t.setPosition(tar_pos, mode=viz.ABS_GLOBAL)
			
			# Preview only: highlight each center target
			if tgt[0] == 0.0 and tgt[1] == 0.0:
				t.color([0.0, 1.0, 0.0])
			
			t.visible(False)
			t_objs[d].append(t)
		
		t_dists.sort(reverse=True)
		for d in t_dists:
			t_planes[d].visible(False)

		# Head-lock the completed target array
		t_link = viz.link(viz.MainView, root, enabled=True)

		# Preview targets, separately for each depth plane
		for d in t_dists:
			t_planes[d].visible(True)
			for t in t_objs[d]:
				t.visible(True)

			dmsg = 'Previewing targets: {:.2f} m distance ({:d}/{:d})'
			self._dlog(dmsg.format(d, len(t_objs[d]), len(targets)))
			yield viztask.waitKeyDown(' ')
			t_planes[d].visible(False)

		# Clear scene objects
		if cursor:
			self._cursor.removeParent(viz.WORLD, scene=self._scene)
			self.showGazeCursor(cursor_state)
		root.remove(children=True)
		viz.MainWindow.setScene(prev_scene)
		self._dlog('Original scene returned')


	def calibrate(self):
		""" Calibrates the eye tracker via its calibrate() method """
		self._dlog('Starting eye tracker calibration.')
		yield self._tracker.calibrate()
		self._dlog('Eye tracker calibration finished.')
	

	def validate(self, targets=None, dur=2000, tar_color=[1.0, 1.0, 1.0], randomize=True, metadata=None):
		""" Measure gaze accuracy and precision for a set of head-locked targets
		in a special validation scene. 
		
		Args:
			targets: One of the following:
				- Target set from vzgazetoolbox.VAL_TAR_*, OR
				- List of targets (x, y, depth), x/y in visual degrees, depth in m
			dur (int): sampling duration per target, in ms
			tar_color (3-tuple): Target sphere color
			randomize (bool): if True, randomize target order in each validation
			metadata (dict): Dict of participant metadata to include with result
		
		Returns: vzgazetoolbox.ValidationResult object 
		"""
		if targets is None:
			if self._default_targets is not None:
				targets = self._default_targets
			else:
				# Central target drift check (default)
				targets = VAL_TAR_C

		# Set up targets in validation scene
		root = viz.addGroup(scene=self._scene)
		t_dists = []
		t_planes = {}
		all_targets = []
		c = 0
		for tgt in targets:
			# Add depth plane if it doesn't exist yet
			d = tgt[2]
			if d not in t_dists:
				t_dists.append(d)
				t_planes[d] = vizshape.addPlane(size=(1000.0, 1000.0), axis=vizshape.AXIS_Z, scene=self._scene,
													 flipFaces=True, color=self.tar_plane_color, parent=root)
				t_planes[d].setPosition([0.0, 0.0, d], mode=viz.REL_PARENT)
			
			# Find target position on depth plane using raycasting
			tar_mat = vizmat.Transform()
			tar_mat.makeEuler([tgt[0], -tgt[1], 0.0])
			tar_dir = tar_mat.getLineForward(1000)
			info = self._scene.intersect(tar_dir.begin, tar_dir.end, ignoreBackFace = False, all=True)
			tar_pos = None
			for obj in info:
				# Only intersect the correct plane
				if obj.object == t_planes[d]:
					tar_pos = obj.point
			t = viz.addGroup(scene=self._scene, parent=root)
			#t_out = vizshape.addSphere(radius=self._deg2m(self.fix_size, d), parent=t, scene=self._scene, color=(1, 1, 1))
			t_out = vizshape.addCylinder(radius=self._deg2m(self.fix_size, d), height=self._deg2m(self.fix_size/20.0, d), parent=t, scene=self._scene, axis=vizshape.AXIS_Z, color=(1, 1, 1))
			t_in = vizshape.addSphere(radius=self._deg2m(self.fix_size/5.0, d), parent=t, scene=self._scene, color=(0,0,0), pos=[0, 0, -self._deg2m(self.fix_size, d)])
			t.setPosition(tar_pos, mode=viz.ABS_GLOBAL)
			t.visible(False)
			tgtHMD = t.getPosition(mode=viz.REL_PARENT) # target in HMD space

			all_targets.append((c, tgt, tgtHMD, t, t_planes[tgt[2]]))
			c += 1

		for d in t_dists:
			t_planes[d].visible(False)

		# Add a background plane to prevent screen color switching between targets
		bg = vizshape.addPlane(size=(1000.0, 1000.0), axis=vizshape.AXIS_Z, scene=self._scene,
							   flipFaces=True, color=self.tar_plane_color, parent=root)
		bg.setPosition([0.0, 0.0, max(t_dists) + 1.0], mode=viz.REL_PARENT)

		# Head-lock the completed target array and switch scenes
		t_link = viz.link(viz.MainView, root, enabled=True)
		prev_scene = viz.MainWindow.getScene()
		viz.MainWindow.setScene(self._scene)
		self._dlog('Validation scene set up complete')
		
		# Initialize validation recorder
		val_recorder = vizact.onupdate(-1, self._record_val_sample)
		val_recorder.setEnabled(False)
		self._val_samples = [] # task starts out enabled, so might have recorded a stray sample
		
		if randomize:
			cal_targets = random.sample(all_targets, len(all_targets))
		else:
			cal_targets = all_targets

		# Calculate data quality measures per target
		tar_data = []
		sam_data = []
		for (c, tarpos, tgtHMD, ct, tplane) in cal_targets:

			d = {}

			# Record gaze samples
			yield viztask.waitTime(1.0)
			val_recorder.setEnabled(True)
			if self.recording:
				self.recordEvent('VAL_START {:d} {:.1f} {:.1f} {:.1f}'.format(c, *tarpos))
			tplane.visible(True)
			ct.visible(True)
			
			yield viztask.waitTime(float(dur) / 1000)
			val_recorder.setEnabled(False)
			s = self._get_val_samples()
			ct.color([0.1, 1.0, 0.1])
			yield viztask.waitTime(0.2)
			
			ct.visible(False)
			tplane.visible(False)
			if self.recording:
				self.recordEvent('VAL_END {:d} {:.1f} {:.1f} {:.1f}'.format(c, *tarpos))
			
			# Binocular measures
			delta = []
			deltaX = []
			deltaY = []
			gazeX = []
			gazeY = []

			# Monocular measures, only used when supported
			ipdM = []
			deltaM = [[], []] # monocular as [L, R]
			deltaXM = [[], []]
			deltaYM = [[], []]
			gazeXM = [[], []]
			gazeYM = [[], []]
			
			d['set_no'] = c
			d['x'] =  tarpos[0]
			d['y'] =  tarpos[1]
			d['d'] =  tarpos[2]
			d['xm'] =  tgtHMD[0] # in m 
			d['ym'] =  tgtHMD[1]
			
			# Select stable fixation samples
			# TODO: use actual fixation detector here!
			s = s[20:]

			for sam in s:
				# Calculate gaze-target angular errors in HMD space
				gazeOri = (sam['tracker_posX'], sam['tracker_posY'], sam['tracker_posZ'])
				eyeTarVec = vizmat.VectorToPoint(gazeOri, tgtHMD)
				eyeGazeVec = (sam['trackVec_X'], sam['trackVec_Y'], sam['trackVec_Z'])

				angularDiff = vizmat.Transform()
				angularDiff.makeVecRotVec(eyeTarVec, eyeGazeVec)
				(dX, dY, _) = angularDiff.getEuler()
				dY = -dY
				sam['targetErr_X'], sam['targetErr_Y'] = dX, dY

				delta.append(vizmat.AngleBetweenVector(eyeGazeVec, eyeTarVec))
				deltaX.append(dX)
				deltaY.append(dY)

				# Average gaze angle in HMD space
				eyeHeadVec = (sam['trackVec_X'], sam['trackVec_Y'], sam['trackVec_Z'])
				eyeHeadRot = vizmat.Transform()
				eyeHeadRot.makeVecRotVec([0, 0, 1], eyeHeadVec)
				(gX, gY, _) = eyeHeadRot.getEuler()
				gY = -gY

				gazeX.append(gX)
				gazeY.append(gY)
				sam['targetGaze_X'], sam['targetGaze_Y'] = gX, gY

				# Monocular data, if available
				if self._tracker_has_eye_flag:
					ipdM.append(abs(sam['trackerR_posX'] - sam['trackerL_posX']) * 1000.0)
					for eyei, eye in enumerate(['L', 'R']):
						# Angular gaze-target errors
						gazeOriM = (sam['tracker{:s}_posX'.format(eye)],
									sam['tracker{:s}_posY'.format(eye)],
									sam['tracker{:s}_posZ'.format(eye)])
						eyeTarVecM = vizmat.VectorToPoint(gazeOriM, tgtHMD)
						eyeGazeVecM = (sam['trackVec{:s}_X'.format(eye)],
									   sam['trackVec{:s}_Y'.format(eye)],
									   sam['trackVec{:s}_Z'.format(eye)])
						
						angularDiffM = vizmat.Transform()
						angularDiffM.makeVecRotVec(eyeTarVecM, eyeGazeVecM)
						(dXM, dYM, _) = angularDiff.getEuler()
						dYM = -dYM
						
						sam['targetErr{:s}_X'.format(eye)] = dXM
						sam['targetErr{:s}_Y'.format(eye)] = dYM
						deltaM[eyei].append(vizmat.AngleBetweenVector(eyeGazeVecM, eyeTarVecM))
						deltaXM[eyei].append(dXM)
						deltaYM[eyei].append(dYM)

						# Average gaze angles
						eyeHeadVecM = (sam['trackVec{:s}_X'.format(eye)], 
									   sam['trackVec{:s}_Y'.format(eye)], 
									   sam['trackVec{:s}_Z'.format(eye)])
						eyeHeadRotM = vizmat.Transform()
						eyeHeadRotM.makeVecRotVec([0, 0, 1], eyeHeadVecM)
						(gXM, gYM, _) = eyeHeadRotM.getEuler()
						gYM = -gYM
						
						sam['targetGaze{:s}_X'.format(eye)] = gXM
						sam['targetGaze{:s}_Y'.format(eye)] = gYM
						gazeXM[eyei].append(gXM)
						gazeYM[eyei].append(gYM)

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

			# Monocular measures and IPD
			if self._tracker_has_eye_flag:
				d['ipd'] = mean(ipdM)
				for eyei, eye in enumerate(['L', 'R']):
					d['avgX_{:s}'.format(eye)] = mean(gazeXM[eyei])
					d['avgY_{:s}'.format(eye)] = mean(gazeYM[eyei])
					d['medX_{:s}'.format(eye)] = median(gazeXM[eyei])
					d['medY_{:s}'.format(eye)] = median(gazeYM[eyei])
					d['offX_{:s}'.format(eye)] = mean(deltaXM[eyei])
					d['offY_{:s}'.format(eye)] = mean(deltaYM[eyei])
					d['acc_{:s}'.format(eye)] = mean(deltaM[eyei])
					d['accX_{:s}'.format(eye)] = mean([abs(v) for v in deltaXM[eyei]])
					d['accY_{:s}'.format(eye)] = mean([abs(v) for v in deltaYM[eyei]])
					d['medacc_{:s}'.format(eye)] = median(deltaM[eyei])
					d['medaccX_{:s}'.format(eye)] = median([abs(v) for v in deltaXM[eyei]])
					d['medaccY_{:s}'.format(eye)] = median([abs(v) for v in deltaYM[eyei]])
					d['sd_{:s}'.format(eye)] = sd(deltaM[eyei])
					d['sdX_{:s}'.format(eye)] = sd(deltaXM[eyei])
					d['sdY_{:s}'.format(eye)] = sd(deltaYM[eyei])
					d['rmsi_{:s}'.format(eye)] = rmsi(deltaM[eyei])
					d['rmsiX_{:s}'.format(eye)] = rmsi(deltaXM[eyei])
					d['rmsiY_{:s}'.format(eye)] = rmsi(deltaYM[eyei])

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

		# Clear and return to previous scene
		root.remove(children=True)
		viz.MainWindow.setScene(prev_scene)
		self._dlog('Original scene returned')

		# Store participant metadata
		rmeta = {'datetime': time.strftime('%d.%m.%Y %H:%M:%S', time.localtime()),
				 'label': 	 'validation',
				 'version':  0.1}
		if metadata is not None:
			rmeta.update(metadata)

		rv = ValidationResult(result=avg_data, samples=sam_data, targets=tar_data, metadata=rmeta)
		if self.recording:
				self.recordEvent('VAL_RESULT {:.2f} {:.2f} {:.2f}'.format(d['acc'], d['rmsi'], d['sd']))

		self._last_val_result = rv
		viztask.returnValue(self._last_val_result)


	def _onUpdate(self):
		""" Task callback that runs on each display frame. Always updates 
		current gaze data properties, triggers sample recording if recording is on.
		"""
		if self._force_update:
			viz.update(viz.UPDATE_PLUGINS | viz.UPDATE_LINKS)

		time_ms = viz.tick() * 1000.0		# Vizard time
		frame = viz.getFrameNumber()		# Vizard frame number
		clock = perf_counter() * 1000.0 		# Python system time

		# Gaze and view nodes
		cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
		gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
		gW = copy.deepcopy(gT)				# Gaze-in-World FoR
		gW.postMult(cW)
		self._gazedir = gW
		nodes = {'tracker': gT,
				 'view':	cW,
				 'gaze': 	gW}

		# Monocular data, if available
		if self._tracker_has_eye_flag:
			gTL = self._tracker.getMatrix(flag=viz.LEFT_EYE)
			gTR = self._tracker.getMatrix(flag=viz.RIGHT_EYE)
			gWL = copy.deepcopy(gTL)
			gWR = copy.deepcopy(gTR)
			gWL.postMult(cW)
			gWR.postMult(cW)
			nodes['trackerL'] = gTL
			nodes['trackerR'] = gTR
			nodes['gazeL'] = gWL
			nodes['gazeR'] = gWR
		
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
			# Additional tracked nodes
			for obj in self._tracked_nodes.keys():
				nodes[obj] = self._tracked_nodes[obj].getMatrix()

			sample = ((time_ms, frame, clock), nodes)
			self.recordSample(sample=sample)


	def recordSample(self, console=False, sample=None):
		""" Records transform matrices for head, gaze and tracked objects for the
		current sample. Can also be called manually to record a single frame.
		
		Args:
			console (bool): if True, print logged value to Vizard console
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
			s['systime'] = perf_counter() * 1000.0

			gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
			cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
			gW = copy.deepcopy(gT)				# Gaze-in-World FoR
			gW.postMult(cW)
			nodes = {'tracker': gT,	
					 'view':	cW,
					 'gaze': 	gW}

			if self._tracker_has_eye_flag:
				gTL = self._tracker.getMatrix(flag=viz.LEFT_EYE)
				gTR = self._tracker.getMatrix(flag=viz.RIGHT_EYE)
				gWL = copy.deepcopy(gTL)
				gWR = copy.deepcopy(gTR)
				gWL.postMult(cW)
				gWR.postMult(cW)
				nodes['trackerL'] = gTL
				nodes['trackerR'] = gTR
				nodes['gazeL'] = gWL
				nodes['gazeR'] = gWR
			
			for obj in self._tracked_nodes.keys():
				nodes[obj] = self._tracked_nodes[obj].getMatrix()

		# Store position and orientation data
		for lbl, node_matrix in nodes.items():
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
		s['gaze3d_posY'] = self._gaze3d[1]
		s['gaze3d_posZ'] = self._gaze3d[2]
		if self._gaze3d_valid:
			s['gaze3d_valid'] = 1
			s['gaze3d_object'] = str(self._gaze3d_intersect)
		else:
			s['gaze3d_valid'] = 0
			s['gaze3d_object'] = ''

		# Device-specific eye tracking data
		if self._tracker_type == 'ViveProEyeTracker':
			s['pupil_size'] = self._tracker.getPupilDiameter(viz.BOTH_EYE)
			s['pupil_sizeL'] = self._tracker.getPupilDiameter(viz.LEFT_EYE)
			s['pupil_sizeR'] = self._tracker.getPupilDiameter(viz.RIGHT_EYE)
			s['eye_state'] = self._tracker.getEyeOpen(viz.BOTH_EYE)
			s['eye_stateL'] = self._tracker.getEyeOpen(viz.LEFT_EYE)
			s['eye_stateR'] = self._tracker.getEyeOpen(viz.RIGHT_EYE)

		# Add to preallocated list, or switch to appending if full
		if self._samples_idx < self._prealloc:
			self._samples[self._samples_idx] = s
			self._samples_idx += 1
		else:
			self._samples.append(s)

		if console:
			# Note: printing coordinates will likely slow down rendering! Use for debugging only.
			cWp = cW.getPosition()
			cWd = cW.getEuler()
			gWp = gW.getPosition()
			gWd = gW.getEuler()
			pupilDia = self.MISSING
			if 'pupil_size' in s.keys():
				pupilDia = s['pupil_size']
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
		

	def saveRecording(self, sample_file=None, event_file=None, clear_samples=True, clear_events=True, 
					  sep='\t', quat=False):
		""" Save current gaze recording to a tab-separated CSV file 
		and clear the current recording by default.
		
		Args:
			sample_file: Name of output file to write gaze samples to
			event_file: Name of output file to write event data to
			clear_samples (bool): if True, clear recorded samples after saving
			clear_events (bool): if True, clear recorded events after saving
			sep (str): Field separator in output file
			quat (bool): if True, also export rotation Quaternions
		"""
		# Samples: select keys to be exported and build file format
		fields = ['time', 'systime', 'view_posX', 'view_posY', 'view_posZ', 'view_dirX', 'view_dirY', 'view_dirZ',
				  'gaze_posX', 'gaze_posY', 'gaze_posZ', 'gaze_dirX', 'gaze_dirY', 'gaze_dirZ',
				  'gaze3d_valid', 'gaze3d_posX', 'gaze3d_posY', 'gaze3d_posZ', 'gaze3d_object']
		fmt = ['{:.4f}', '{:.4f}'] + ['{:.5f}',] * 12 + ['{:d}',] + ['{:.5f}',] * 3 + ['"{:s}"',]

		# Tracker-specific fields (not always available)
		special = ['gazeL_posX', 'gazeL_posY', 'gazeL_posZ', 'gazeL_dirX', 'gazeL_dirY', 'gazeL_dirZ',
				   'gazeR_posX', 'gazeR_posY', 'gazeR_posZ', 'gazeR_dirX', 'gazeR_dirY', 'gazeR_dirZ',
				   'pupil_size', 'pupil_sizeL', 'pupil_sizeR', 'eye_state', 'eye_stateL', 'eye_stateR']
		for field in special:
			if field in self._samples[0].keys():
				fields += [field,]
				fmt += ['{:.5f}',]

		# Additional tracked nodes
		for lbl in self._tracked_nodes.keys():
			fields += ['{:s}_posX'.format(lbl), '{:s}_posY'.format(lbl), '{:s}_posZ'.format(lbl), 
					   '{:s}_dirX'.format(lbl), '{:s}_dirY'.format(lbl), '{:s}_dirZ'.format(lbl)]
			fmt += ['{:.5f}',] * 6
		
		# Quaternions (optional)
		if quat:
			fields += ['view_quatX', 'view_quatY', 'view_quatZ', 'view_quatW',
					   'gaze_quatX', 'gaze_quatY', 'gaze_quatZ', 'gaze_quatW']
			fmt += ['{:.5f}',] * 8
			for lbl in self._tracked_nodes.keys():
				fields += ['{:s}_quatX'.format(lbl), '{:s}_quatY'.format(lbl), '{:s}_quatZ'.format(lbl), '{:s}_quatW'.format(lbl)]
				fmt += ['{:.5f}',] * 4
		
		if self.debug:
			fields += ['tracker_posX', 'tracker_posY', 'tracker_posZ', 'tracker_dirX', 'tracker_dirY', 'tracker_dirZ']
			fmt += ['{:.5f}',] * 6
			if self._tracker_has_eye_flag:
				fields += ['trackerL_posX', 'trackerL_posY', 'trackerL_posZ', 'trackerL_dirX', 'trackerL_dirY', 'trackerL_dirZ',
						   'trackerR_posX', 'trackerR_posY', 'trackerR_posZ', 'trackerR_dirX', 'trackerR_dirY', 'trackerR_dirZ']
				fmt += ['{:.5f}',] * 12

			if quat:
				fields += ['tracker_quatX', 'tracker_quatY', 'tracker_quatZ', 'tracker_quatW']
				fmt += ['{:.5f}',] * 4
				if self._tracker_has_eye_flag:
					fields += ['trackerL_quatX', 'trackerL_quatY', 'trackerL_quatZ', 'trackerL_quatW',
							   'trackerR_quatX', 'trackerR_quatY', 'trackerR_quatZ', 'trackerR_quatW']
					fmt += ['{:.5f}',] * 8


		HEADER = sep.join(fields) + '\n'
		ROWFMT = sep.join(fmt) + '\n'
		
		# Events: build header
		evfields = ['time', 'message']
		EHEADER = sep.join(evfields) + '\n'
		EROWFMT = sep.join(['{:.4f}', '"{:s}"']) + '\n'
		
		if sample_file is not None:

			# Cut recording to size if below preallocation limit
			if self._samples_idx < self._prealloc:
				self._samples = self._samples[0:self._samples_idx]
			
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
			self._dlog('Neither sample_file nor event_file were specified. No data saved.')
		else:
			if clear_samples or clear_events:
				self.clearRecording(samples=clear_samples, events=clear_events)


	def clearRecording(self, samples=True, events=True):
		""" Stops recording and clears both samples and events 
		
		Args:
			samples (bool): if True, clear sample data
			events (bool): if True, clear event data
		"""
		self.recording = False
		dtypes = []
		if samples:
			self._samples = [None,] * self._prealloc
			self._samples_idx = 0
			dtypes.append('samples')
		if events:
			self._events = []
			dtypes.append('events')
		self._dlog('Cleared recording data ({:s})'.format(str(dtypes)))

