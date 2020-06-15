
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
	
	def __init__(self, eyetracker, DEBUG=False):
		""" Eye movement recording and accuracy/precision measurement class.

		Args:
			eyetracker: Vizard extension sensor object representing an eye tracker
			DEBUG (bool): if True, print debug output to console
		"""
		
		self._tracker = eyetracker
		self._tracker_type = type(eyetracker).__name__
		self.debug = DEBUG
		
		# Gaze data recording
		self.recording = False
		self._samples = []
		self._val_samples = []
		self._events = []
		self._recorder = None
		
		# Gaze validation
		self._scene = viz.addScene()
		self.fix_size = 0.5 # radius in degrees
		
		
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

		
		
	def recordSample(self, console=False, is_val=False):
		""" Record the current gaze sample
		Can be called manually or e.g. in vizact.onupdate()
		
		Args:
			console (bool): if True, print logged value to Vizard console
			is_val (bool): if True, record to validation dataset (internal use)
		"""		
		gT = self._tracker.getMatrix() 	# gaze in tracker reference frame
		gTpos = gT.getPosition()		# gaze-in-tracker: eye position
		gTdir = gT.getEuler()			# gaze-in-tracker: eye orientation
		
		cW = viz.MainView.getMatrix()  	# camera in world reference frame
		cWpos = cW.getPosition()		# camera-in-world: MainView position
		cWdir = cW.getEuler()			# camera-in-world: MainView orientation
		
		# Note that this assigns a reference to gW by default, so the gaze-in-tracker
		# matrix is gone. If gT is necessary after this point, copy.deepcopy() in the future!
		gW = gT
		gW.postMult(cW) 		   	   	# gaze in world reference frame
		gWpos = gW.getPosition()		# gaze-in-world: eye position
		gWdir = gW.getEuler()			# gaze-in-world: eye orientation
		
		# Find 3D gaze point through ray intersection method
		g3D = [-1.0, -1.0, -1.0]
		g3D_line = gW.getLineForward(1000)
		g3D_test = viz.intersect(g3D_line.begin, g3D_line.end)
		if g3D_test.valid:
			g3D = g3D_test.point		# gaze-in-world: intersection point
				
		# Pupil size measurement is tracker-specific
		pupilDia = -1.0
		if self._tracker_type == 'ViveProEyeTracker':
			pupilDia = self._tracker.getPupilDiameter()
		
		data = [viz.tick(),
				viz.getFrameNumber(),
				gTpos[0], gTpos[1], gTpos[2],
				gTdir[0], gTdir[1], gTdir[2],
				cWpos[0], cWpos[1], cWpos[2],
				cWdir[0], cWdir[1], cWdir[2],
				gWpos[0], gWpos[1], gWpos[2],
				gWdir[0], gWdir[1], gWdir[2],
				pupilDia,
				g3D[0], g3D[1], g3D[2]]
		
		if is_val:
			self._val_samples.append(data)
		else:
			self._samples.append(data)
		
		if console:
			outformat = '{:.4f} {:d}\tcamXYZ=({:.3f}, {:.3f}, {:.3f}),\tcamDIR=({:.3f}, {:.3f}, {:.3f}),\tgazeXYZ=({:.3f}, {:.3f}, {:.3f}),\tgazeDIR=({:.3f}, {:.3f}, {:.3f}), p={:.3f}'
			print(outformat.format(*data[0:20]))
		
		
	def recordEvent(self, event=''):
		""" Record a time-stamped event string
		
		Args:
			event (str): event string to log
		"""
		ev = [viz.tick(), viz.getFrameNumber(), str(event)]
		self._events.append(ev)

		
	def startRecording(self):
		""" Start recording of gaze samples and events """
		if self._recorder is None:
			self._recorder = vizact.onupdate(0, self.recordSample)
		if not self.recording:
			self._recorder.setEnabled(True)
			self.recording = True
			self.recordEvent('REC_START')
			self._dlog('Recording started.')
		
		
	def stopRecording(self):
		""" Stop recording of gaze samples and events """
		if self.recording:
			if self._recorder is not None:
				self._recorder.setEnabled(False)
			self.recording = False
			self.recordEvent('REC_STOP')
			self._dlog('Recording stopped.')
		
		
	def saveRecording(self, sample_file=None, event_file=None, clear=True, sep='\t'):
		""" Save current gaze recording to a tab-separated CSV file 
		and clear the current recording by default.
		
		Args:
			sample_file: Name of output file to write gaze samples to
			event_file: Name of output file to write event data to
			clear (bool): if True, clear current recording after saving
			sep (str): Field separator in output file
		"""
		HEADER = sep.join(['tick', 'frame', 'gTposX', 'gTposY', 'gTposZ', 'gTdirX', 'gTdirY', 'gTdirZ', 'cWposX', 'cWposY', 'cWposZ',
				  'cWdirX', 'cWdirY', 'cWdirZ', 'gWposX', 'gWposY', 'gWposZ', 'gWdirX', 'gWdirY', 'gWdirZ',
				  'pDia', 'gaze3Dx', 'gaze3Dy', 'gaze3Dz']) + '\n'
		ROW = sep.join(['{:.4f}', '{:d}'] + ['{:.10f}',] * 18 + ['{:.4f}'] + ['{:.10f}',] * 3) + '\n'
		
		EHEADER = sep.join(['tick', 'frame', 'event']) + '\n'
		EROW = sep.join(['{:.4f}', '{:d}', '"{:s}"']) + '\n'
		
		if sample_file is not None:
			n = 0
			with open(sample_file, 'w') as of:
				of.write(HEADER)
				for row in self._samples:
					of.write(ROW.format(*row))
					n += 1
			self._dlog('Saved {:d} samples to file: {:s}'.format(n, sample_file))
		
		if event_file is not None:
			n = 0
			with open(event_file, 'w') as ef:
				ef.write(EHEADER)
				for ev in self._events:
					ef.write(EROW.format(*ev))
					n += 1
			self._dlog('Saved {:d} events to file: {:s}'.format(n, event_file))
		
		if sample_file is None and event_file is None:
			self._dlog('Neither sample_file or event_file were specified. No data saved.')



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
				self._samples = recorder._samples

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
				self._ui_bar.message('No data'.format(self._frame, len(self._samples)))
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
