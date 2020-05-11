
import math
import random

import viz
import vizact
import viztask
import vizshape


class VzGazeRecorder():
	
	def __init__(self, eyetracker, DEBUG=False):
		""" Eye movement recording and accuracy/precision measurement class.

		Args:
			eyetracker: Vizard extension sensor object representing an eye tracker
			DEBUG (bool): if True, print debug output to console
		"""
		
		self._tracker = eyetracker
		self.debug = DEBUG
		
		# Gaze data recording
		self.recording = False
		self._samples = []
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
		
		
	def record_sample(self, console=False):
		""" Record the current gaze sample
		Can be called manually or e.g. in vizact.onupdate()
		
		Args:
			console (bool): if True, print logged value to Vizard console 
		"""
		gT = self._tracker.getMatrix() # gaze in tracker reference frame
		cW = viz.MainView.getMatrix()  # camera in world reference frame 
		gW = gT
		gW.postMult(cW) 		   	   # gaze in world reference frame
		
		# TODO: add code to log 3D intersection gaze point
		# TODO: add valid flag to log 
		#g3D = gW.getLineForward(1000)
		#scene.intersect(line)		
		
		gTpos = gT.getPosition()
		gTdir = gT.getForward()
		cWpos = cW.getPosition()
		cWdir = cW.getForward()
		gWpos = gW.getPosition()
		gWdir = gW.getForward()
		
		data = [viz.tick(),
				viz.getFrameNumber(),
				gTpos[0], gTpos[1], gTpos[1],
				gTdir[0], gTdir[1], gTdir[1],
				cWpos[0], cWpos[1], cWpos[1],
				cWdir[0], cWdir[1], cWdir[1],
				gWpos[0], gWpos[1], gWpos[1],
				gWdir[0], gWdir[1], gWdir[1],
				self._tracker.getPupilDiameter(),
				-1, -1, -1]
		self._samples.append(data)
		
		if console:
			outformat = '{:.4f} {:d}\tcamXYZ=({:.3f}, {:.3f}, {:.3f}),\tcamDIR=({:.3f}, {:.3f}, {:.3f}),\tgazeXYZ=({:.3f}, {:.3f}, {:.3f}),\tgazeDIR=({:.3f}, {:.3f}, {:.3f}), p={:.3f}'
			print(outformat.format(*data[0:20]))
		
		
	def record_event(self, event=''):
		""" Record a time-stamped event string
		
		Args:
			event (str): event string to log
		"""
		ev = [viz.tick(), viz.getFrameNumber(), str(event)]
		self._events.append(ev)

		
	def start_recording(self):
		""" Start recording of gaze samples and events """
		if self._recorder is None:
			self._recorder = vizact.onupdate(10, self.record_sample)
		self._recorder.setEnabled(True)
		self.recording = True
		self.record_event('start_recording')
		self._dlog('Recording started.')
		
		
	def stop_recording(self):
		""" Stop recording of gaze samples and events """
		if self._recorder is not None:
			self._recorder.setEnabled(False)
		self.recording = False
		self.record_event('stop_recording')
		self._dlog('Recording stopped.')
		
		
	def save_recording(self, sample_file='vzgaze.csv', event_file=None, clear=True, sep='\t'):
		""" Save current gaze recording to a tab-separated CSV file 
		and clear the current recording by default.
		
		Args:
			sample_file: Name of output file to write gaze samples to
			event_file: Optional name of file to write event data to
			clear (bool): if True, clear current recording after saving
			sep (str): Field separator in output file
		"""
		HEADER = sep.join(['tick', 'frame', 'eyeTx', 'eyeTy', 'eyeTz', 'gazeTx', 'gazeTy', 'gazeTz', 'camWx', 'camWy', 'camWy', 
				  'viewWx', 'viewWx', 'viewWx', 'eyeWx', 'eyeWx', 'eyeWx', 'gazeWx', 'gazeWx', 'gazeWx', 
				  'pDia', 'gaze3Dx', 'gaze3Dy', 'gaze3Dz']) + '\n'
		ROW = sep.join(['{:.4f}', '{:d}'] + ['{:.10f}',] * 18 + ['{:.4f}'] + ['{:.10f}',] * 3) + '\n'
		
		EHEADER = sep.join(['tick', 'frame', 'event']) + '\n'
		EROW = sep.join(['{:.4f}', '{:d}', '"{:s}"']) + '\n'
		
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


class Eyeball(viz.VizNode):
	""" Simple eyeball object to visually indicate gaze direction """
	
	def __init__(self, radius=0.024, eyecolor='blue', pointer=False, gaze_length=100):
		""" Initialize a new Eyeball node
		
		Args:
			radius (float): Eyeball radius in m
			eyecolor (str, 3-tuple): Iris color for this eye (see setEyeColor)
			pointer (bool): if True, start out the gaze pointer visible
			gaze_length (float): length of gaze pointer in m
		"""

		self.eyecolors = {'brown': [0.387, 0.305, 0.203],
						  'blue':  [0.179, 0.324, 0.433],
						  'green': [0.109, 0.469, 0.277],
						  'grey':  [0.285, 0.461, 0.395]}
		
		eye = viz.addChild('unit_eye.gltf')
		viz.VizNode.__init__(self, eye.id)
		
		# Add gaze direction pointer (invisible by default)
		self.pointer = vizshape.addCylinder(height=gaze_length, radius=0.05,
												 axis=vizshape.AXIS_Z, parent=eye)
		self.pointer.setPosition([0.0, 0.0, gaze_length/2])
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
