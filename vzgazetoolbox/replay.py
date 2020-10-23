# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Gaze and object position and orientation replay class

import random

import viz
import vizact
import vizinfo
import vizshape

from .eyeball import Eyeball

class VzGazeReplay():
	
	def __init__(self, recording=None, ui=True, eyeball=True, console=False, eye='BINOCULAR'):
		""" Gaze and object position and orientation replay class
		
		Args:
			recording: file name of a CSV recording file to load, OR
				VzGazeRecorder instance to get sample data from
			ui (bool): if True, display a vizinfo panel with replay status
			eyeball (bool): if True, show Eyeball shape, else use axes object
			console (bool): if True, print timing and position data of current frame to console
			eye: controls how to show eye position and gaze data:
				- viz.LEFT_EYE or "LEFT_EYE": show only left eye gaze data
				- viz.RIGHT_EYE or "RIGHT_EYE": show only right eye gaze data
				- viz.BOTH_EYE or "BOTH_EYE": show only the averaged (cyclopean) gaze data
				- "BINOCULAR": show both eyes with individual gaze data (default if available)
				Note: "BOTH_EYE" will be used if input file only contains averaged gaze data!
		"""
		# Visualization objects
		if eyeball:
			self._eye1 = Eyeball(visible=False, pointer=True)
			self._eye2 = Eyeball(visible=False, pointer=True)
		else:
			self._eye1 = vizshape.addAxes(scale=[0.1, 0.1, 0.1])
			self._eye2 = vizshape.addAxes(scale=[0.1, 0.1, 0.1])
		self.initial_eye_pos = [0.0, 0.0, 0.0]
		
		self._frame = 0
		self._samples = []
		self._sample_time_offset = 0.0
		self._player = None
		self.replaying = False
		self.finished = False
		self.console = console

		self.replay_nodes = []
		self._nodes = {}

		if eye == viz.LEFT_EYE:
			self.eye = 'LEFT_EYE'
		elif eye == viz.RIGHT_EYE:
			self.eye = 'RIGHT_EYE'
		elif eye == viz.BOTH_EYE:
			self.eye = 'BOTH_EYE'
		else:
			self.eye = eye
		if self.eye not in ['LEFT_EYE', 'RIGHT_EYE', 'BOTH_EYE', 'BINOCULAR']:
			raise ValueError('Unknown eye parameter specified: {:s}'.format(self.eye))

		# Set up status GUI
		self._ui = None
		if ui:
			self._ui = vizinfo.InfoPanel('Gaze Data Replay', align=viz.ALIGN_RIGHT_TOP)
			self._ui_bar = self._ui.addItem(viz.addProgressBar('0/0'))
			self._ui_time = self._ui.addLabelItem('Time', viz.addText('NA'))
			self._ui.addSeparator()
			self._ui.addItem(viz.addText('Available Nodes:'))
			self._set_ui()

		# Load recording
		if recording is not None:
			if type(recording) == str:
				self.loadRecording(recording)
			else:
				self._samples = recording._samples


	def _set_ui(self):
		""" Set GUI elements to display status (if enabled) """
		if self._ui is not None:

			if len(self._samples) == 0:
				self._ui_bar.message('No data')
			else:
				self._ui_bar.set(float(self._frame)/float(len(self._samples)))
				self._ui_bar.message('{:d}/{:d}'.format(self._frame, len(self._samples)))

				t = self._samples[self._frame]['time'] - self._sample_time_offset
				if t > 10000:
					self._ui_time.message('{:.1f} s'.format(t/1000.0))
				else:
					self._ui_time.message('{:.1f} ms'.format(t))


	def _ui_set_node_visibility(self, node):
		""" Callback to update node visibility on checkbox change """
		check = self._nodes[node]['ui'].get()
		self._nodes[node]['visible'] = bool(check)
		self._nodes[node]['obj'].visible(bool(check))
	

	def _update_nodes(self):
		""" Create replay node objects and UI items """
		COLORS = [viz.GREEN, viz.BLUE, viz.YELLOW, viz.GRAY, viz.WHITE]
		COLOR_IDX = 0

		# Remove all previous checkbox UI objects
		if self._ui is not None: 
			for node in self._nodes.keys():
				self._nodes[node]['ui'].remove()
		self._nodes = {}

		for node in self.replay_nodes:
			self._nodes[node] = {'visible': True}
			if node == 'gaze3d':
				# Gaze3d is always red for consistency
				self._nodes[node]['color'] = [1.0, 0.0, 0.0]
			else:
				self._nodes[node]['color'] = COLORS[COLOR_IDX]
				COLOR_IDX += 1
				if COLOR_IDX > len(COLORS):
					COLOR_IDX = 0
			self._nodes[node]['obj'] = vizshape.addSphere(radius=0.01, color=self._nodes[node]['color'])

			if self._ui is not None:
				self._nodes[node]['ui'] = self._ui.addLabelItem(node, viz.addCheckbox())
				self._nodes[node]['ui'].label.color(self._nodes[node]['color'])
				self._nodes[node]['ui'].set(1)
				self._nodes[node]['callback'] = vizact.onbuttonup(self._nodes[node]['ui'], self._ui_set_node_visibility, node)
				self._nodes[node]['callback'] = vizact.onbuttondown(self._nodes[node]['ui'], self._ui_set_node_visibility, node)


	def loadRecording(self, sample_file, sep='\t'):
		""" Load a VzGazeRecorder sample file for replay
		
		Args:
			sample_file (str): Filename of CSV file to load
			sep (str): Field separator in CSV input file
		"""
		s = []
		HEADER = []
		with open(sample_file, 'r') as sf:
			HEADER = sf.readline().strip('\n').split(sep)
			
			for line in sf.readlines():
				sample = {}
				l = line.split(sep)
				for idx, field in enumerate(HEADER):
					try:
						sample[field] = float(l[idx])
					except ValueError:
						sample[field] = l[idx]
				s.append(sample)

		self._samples = s
		self._sample_time_offset = s[0]['time']
		self.initial_eye_pos = [s[0]['gaze_posX'], s[0]['gaze_posY'], s[0]['gaze_posZ']]

		# Find tracked nodes
		_nodes_builtin = ['view', 'gaze', 'gazeL', 'gazeR', 'tracker', 'trackerL', 'trackerR']
		for field in HEADER:
			if field[-5:] == '_posX' and field[0:-5] not in _nodes_builtin:
				self.replay_nodes.append(field[0:-5])
		self._update_nodes()
		self._set_ui()
		print('* Loaded {:d} replay samples from {:s}.'.format(len(s), sample_file))
		if len(self.replay_nodes) > 1:
			print('* Replay contains {:d} tracked nodes: {:s}.'.format(len(self.replay_nodes), ', '.join(self.replay_nodes)))

		# Check if data is binocular or monocular, adjust display settings
		if 'gazeL_posX' not in HEADER and 'gazeR_posX' not in HEADER:
			if self.eye != 'BOTH_EYE':
				self.eye = 'BOTH_EYE'
				print('* Note: no individual eye data present in input file, falling back to averaged gaze data!')


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
			self._eye1.visible(True)
			if self.eye == 'BINOCULAR':
				self._eye2.visible(True)
			print('Replay started.')

		
	def stopReplay(self):
		""" Stop an ongoing replay """
		if self.replaying:
			if self._player is not None:
				self._player.setEnabled(False)
			self.replaying = False
			self._eye1.visible(False)
			self._eye2.visible(False)
			print('Replay stopped at frame {:d}.'.format(self._frame))


	def resetReplay(self):
		""" Stop replay and reset to first frame """
		if self.replaying:
			self.stopReplay()
		self._frame = 0
		self._set_ui()


	def replayCurrentFrame(self, advance=True):
		""" Replay task. Sets up gaze position for each upcoming frame 
		
		Args:
			advance (bool): if True, advance to next frame (default).
		"""
		f = self._samples[self._frame]

		# Set up eye representation(s)
		if self.eye == 'LEFT_EYE':
			eye_mat = viz.Matrix()
			eye_mat.setEuler([f['gazeL_dirX'], f['gazeL_dirY'], f['gazeL_dirZ']])
			eye_mat.setPosition([f['gazeL_posX'], f['gazeL_posY'], f['gazeL_posZ']])
			eye_mat.setScale(self._eye1.getScale())
			self._eye1.setMatrix(eye_mat)

		elif self.eye == 'RIGHT_EYE':
			eye_mat = viz.Matrix()
			eye_mat.setEuler([f['gazeR_dirX'], f['gazeR_dirY'], f['gazeR_dirZ']])
			eye_mat.setPosition([f['gazeR_posX'], f['gazeR_posY'], f['gazeR_posZ']])
			eye_mat.setScale(self._eye1.getScale())
			self._eye1.setMatrix(eye_mat)

		elif self.eye == 'BOTH_EYE':
			eye_mat = viz.Matrix()
			eye_mat.setEuler([f['gaze_dirX'], f['gaze_dirY'], f['gaze_dirZ']])
			eye_mat.setPosition([f['gaze_posX'], f['gaze_posY'], f['gaze_posZ']])
			eye_mat.setScale(self._eye1.getScale())
			self._eye1.setMatrix(eye_mat)

		elif self.eye == 'BINOCULAR':
			eyeL_mat = viz.Matrix()
			eyeL_mat.setEuler([f['gazeL_dirX'], f['gazeL_dirY'], f['gazeL_dirZ']])
			eyeL_mat.setPosition([f['gazeL_posX'], f['gazeL_posY'], f['gazeL_posZ']])
			eyeL_mat.setScale(self._eye1.getScale())
			eyeR_mat = viz.Matrix()
			eyeR_mat.setEuler([f['gazeR_dirX'], f['gazeR_dirY'], f['gazeR_dirZ']])
			eyeR_mat.setPosition([f['gazeR_posX'], f['gazeR_posY'], f['gazeR_posZ']])
			eyeR_mat.setScale(self._eye2.getScale())
			self._eye1.setMatrix(eyeL_mat)
			self._eye2.setMatrix(eyeR_mat)

		# Position the 3D gaze cursor and other nodes
		for node in self._nodes.keys():
			if self._nodes[node]['visible']:
				self._nodes[node]['obj'].setPosition([f['{:s}_posX'.format(node)], f['{:s}_posY'.format(node)], f['{:s}_posZ'.format(node)]])

		self._set_ui()
		if self.console:
			st = 't={:.2f}s, f={:d}\tgaze3d=[{:0.2f}, {:0.2f}, {:0.2f}]\tgaze=[{:0.2f}, {:0.2f}, {:0.2f}]'
			print(st.format((f['time'] - self._sample_time_offset)/1000.0, self._frame, f['gaze3d_posX'], f['gaze3d_posY'], f['gaze3d_posZ'], f['gaze_dirX'], f['gaze_dirY'], f['gaze_dirZ']))
		else:
			if self._frame == 0 or self._frame == len(self._samples) or self._frame % 100 == 0:
				print('Replaying frame {:d}/{:d}, t={:.1f} s'.format(self._frame, len(self._samples), 
																	(f['time'] - self._sample_time_offset)/1000.0))

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
		""" Returns True if replay is finished,
			use as viztask.waitTrue(object.replayDone)
		"""
		return self.finished


	def setNodeVisibility(self, node='gaze3d', visible=True):
		""" Controls the visibility of replay nodes, such as 
		the gaze cursor or additional tracked objects.

		Args:
			node (str): node name from self.replay_nodes
			visible (bool): if True, node is set to visible
		"""
		if node not in self.replay_nodes:
			raise ValueError('Unknown node name specified!')

		self._nodes[node]['visible'] = visible
		self._nodes[node]['obj'].visible(visible)
		self._nodes[node]['ui'].set(int(visible))
