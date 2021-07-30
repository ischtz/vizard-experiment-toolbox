# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Gaze and object position and orientation replay class

import csv
import random
import colorsys

import viz
import vizact
import vizinfo
import vizshape

from .eyeball import Eyeball

class SampleReplay(object):
    
    def __init__(self, recording=None, ui=True, eyeball=True, console=False, eye='BINOCULAR',
                 replay_view=True):
        """ Gaze and object position and orientation replay class
        
        Args:
            recording: file name of a CSV recording file to load, OR
                SampleRecorder instance to get sample data from
            ui (bool): if True, display a vizinfo panel with replay status
            eyeball (bool): if True, show Eyeball shape, else use axes object
            console (bool): if True, print timing and position data of current frame to console
            eye: controls how to show eye position and gaze data, if available:
                - viz.LEFT_EYE or "LEFT_EYE": show only left eye gaze data  
                - viz.RIGHT_EYE or "RIGHT_EYE": show only right eye gaze data
                - viz.BOTH_EYE or "BOTH_EYE": show only the averaged (cyclopean) gaze data
                - "BINOCULAR": show both eyes with individual gaze data (default if available)
                    Note: "BOTH_EYE" will be used if input file only contains averaged gaze data!
                - None: do not replay gaze data, even if it is available in the recording
            replay_view (bool): if True, move the MainView with recorded sample data
        """
        # Create gaze visualization nodes
        self._gaze = {'L': {}, 'R': {}, '': {}}
        for eye_pos in list(self._gaze.keys()):
            self._gaze[eye_pos]['data'] = False
            self._gaze[eye_pos]['node'] = None
            self._gaze[eye_pos]['eye'] = Eyeball(visible=False, pointer=True)
            self._gaze[eye_pos]['axes'] = vizshape.addAxes(scale=[0.1, 0.1, 0.1])
            self._gaze[eye_pos]['axes'].visible(False)

        # Initial state of each eye visualization
        if eye not in ['LEFT_EYE', 'RIGHT_EYE', 'BOTH_EYE', 'BINOCULAR', None]:
            raise ValueError('Unknown eye parameter specified: {:s}'.format(eye))
        if eye == viz.LEFT_EYE or eye == 'LEFT_EYE':
            if eyeball:
                self._gaze['L']['node'] = 'eye'
            else:
                self._gaze['L']['node'] = 'axes'
            self._gaze['R']['node'] = None
            self._gaze['']['node'] = None

        elif eye == viz.RIGHT_EYE or eye == 'RIGHT_EYE':
            if eyeball:
                self._gaze['R']['node'] = 'eye'
            else:
                self._gaze['R']['node'] = 'axes'
            self._gaze['L']['node'] = None
            self._gaze['']['node'] = None

        elif eye == viz.BOTH_EYE == 'BOTH_EYE':
            if eyeball:
                self._gaze['']['node'] = 'eye'
            else:
                self._gaze['']['node'] = 'axes'
            self._gaze['L']['node'] = None
            self._gaze['R']['node'] = None

        elif eye == 'BINOCULAR':
            if eyeball:
                self._gaze['L']['node'] = 'eye'
                self._gaze['R']['node'] = 'eye'
            else:
                self._gaze['L']['node'] = 'axes'
                self._gaze['R']['node'] = 'axes'
            self._gaze['']['node'] = None

        elif eye is None:
            self._gaze['L']['node'] = None
            self._gaze['R']['node'] = None
            self._gaze['']['node'] = None

        self._frame = 0
        self._samples = []
        self._sample_time_offset = 0.0
        self._player = None
        self.replaying = False
        self.finished = False
        self.console = console
        self.replay_view = replay_view

        self.replay_nodes = []
        self._nodes = {}

        # Set up status GUI
        self._ui = None
        if ui:
            self._ui = vizinfo.InfoPanel('Sample Data Replay', align=viz.ALIGN_RIGHT_TOP)
            self._ui_bar = self._ui.addItem(viz.addProgressBar('0/0'))
            self._ui_time = self._ui.addLabelItem('Time', viz.addText('NA'))
            self._ui_play = self._ui.addItem(viz.addButtonLabel('Start Replay'))
            vizact.onbuttondown(self._ui_play, self._ui_toggle_replay)
            self._ui.addSeparator()

            self._ui.addItem(viz.addText('Gaze Data'))
            self._gaze['']['ui'] = self._ui.addLabelItem('Combined', viz.addDropList())
            self._gaze['L']['ui'] = self._ui.addLabelItem('Left', viz.addDropList())
            self._gaze['R']['ui'] = self._ui.addLabelItem('Right', viz.addDropList())
            for eye_pos in ['L', 'R', '']:
                self._gaze[eye_pos]['ui'].setLength(0.6)
                self._gaze[eye_pos]['ui'].addItems(['not shown', 'Eyeball', 'Axes'])
                vizact.onlist(self._gaze[eye_pos]['ui'], self._ui_set_gaze)
            self._ui.addSeparator()

            self._ui.addItem(viz.addText('Display Nodes'))
            self._ui_view = self._ui.addLabelItem('Move Viewport', viz.addCheckbox())
            self._ui_view.set(self.replay_view)
            vizact.onbuttonup(self._ui_view, self.setMainViewReplay, False)
            vizact.onbuttondown(self._ui_view, self.setMainViewReplay, True)
            self._set_ui()

        # Load recording
        if recording is not None:
            if type(recording) == str:
                self.loadRecording(recording)
            else:
                self._samples = recording._samples


    def _set_ui(self):
        """ Update GUI elements to display status (if enabled) """
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

            if self.replaying and self._ui_play.getMessage() != 'Pause Replay':
                self._ui_play.message('Pause Replay')
            elif not self.replaying and self._ui_play.getMessage() != 'Start Replay':
                self._ui_play.message('Start Replay')


    def _ui_set_node_visibility(self, node):
        """ Callback for node visibility checkboxes """
        check = self._nodes[node]['ui'].get()
        self._nodes[node]['visible'] = bool(check)
        self._nodes[node]['obj'].visible(bool(check))


    def _ui_toggle_replay(self):
        """ Callback for Play/Pause button """
        if self.replaying:
            self.stopReplay()
        else:
            self.startReplay(from_start=False)


    def _ui_set_gaze(self, event):
        """ Callback for gaze dropdown list """
        for eye_pos in ['L', 'R', '']:
            if event.object == self._gaze[eye_pos]['ui']:
                self._gaze[eye_pos]['eye'].visible(False)
                self._gaze[eye_pos]['axes'].visible(False)
                if event.newSel == 1:
                    self._gaze[eye_pos]['node'] = 'eye'
                    self._gaze[eye_pos]['eye'].visible(True)
                elif event.newSel == 2:
                    self._gaze[eye_pos]['node'] = 'axes'
                    self._gaze[eye_pos]['axes'].visible(True)
                else:
                    self._gaze[eye_pos]['node'] = None


    def _update_nodes(self):
        """ Create replay node objects and UI items """
        COLORS = {'gaze3d': viz.RED, 'view': viz.BLUE}

        # Remove all previous checkbox UI objects
        if self._ui is not None: 
            for node in self._nodes.keys():
                self._nodes[node]['ui'].remove()
        self._nodes = {}

        for node in self.replay_nodes:
            self._nodes[node] = {'visible': True}
            if node in COLORS:
                # Consistent colors for built-in nodes
                self._nodes[node]['color'] = COLORS[node]
            else:
                # Generate a random color
                self._nodes[node]['color'] = colorsys.hsv_to_rgb(random.uniform(0.0, 1.0), 
                                                                 random.uniform(0.4, 1.0), 
                                                                 random.uniform(0.5, 1.0))
            if node == 'view':
                self._nodes[node]['obj'] = vizshape.addAxes(scale=[0.1, 0.1, 0.1], color=self._nodes[node]['color'])
            else:
                self._nodes[node]['obj'] = vizshape.addSphere(radius=0.01, color=self._nodes[node]['color'])

            if self._ui is not None:
                self._nodes[node]['ui'] = self._ui.addLabelItem(node, viz.addCheckbox())
                self._nodes[node]['ui'].label.color(self._nodes[node]['color'])
                self._nodes[node]['ui'].set(1)
                self._nodes[node]['callback'] = vizact.onbuttonup(self._nodes[node]['ui'], self._ui_set_node_visibility, node)
                self._nodes[node]['callback'] = vizact.onbuttondown(self._nodes[node]['ui'], self._ui_set_node_visibility, node)

        # Enable / disable gaze settings based on data availability
        for eye_pos in list(self._gaze.keys()):
            if self._gaze[eye_pos]['data']:
                self._gaze[eye_pos]['ui'].enable()
                if self._gaze[eye_pos]['node'] is None:
                    self._gaze[eye_pos]['ui'].select(0)
                elif self._gaze[eye_pos]['node'] == 'eye':
                    self._gaze[eye_pos]['ui'].select(1)
                elif self._gaze[eye_pos]['node'] == 'axes':
                    self._gaze[eye_pos]['ui'].select(2)
            else:
                self._gaze[eye_pos]['ui'].disable()


    def loadRecording(self, sample_file, sep='\t'):
        """ Load a SampleRecorder sample file for replay
        
        Args:
            sample_file (str): Filename of CSV file to load
            sep (str): Field separator in CSV input file
        """
        s = []
        with open(sample_file, 'r') as sf:
            reader = csv.DictReader(sf, delimiter=sep)
            if len(reader.fieldnames) == 1:
                m = 'Warning: Only a single column read from recording file. Is the field separator set correctly (e.g., sep=";")?\n'
                print(m)

            HEADER = reader.fieldnames
            for row in reader:
                sample = {}
                for field in reader.fieldnames:

                    # Convert numeric values
                    data = row[field]
                    try:
                        sample[field] = int(data)
                    except ValueError:
                        try:
                            sample[field] = float(data)
                        except ValueError:
                            sample[field] = data
                s.append(sample)

        self._samples = s
        self._sample_time_offset = s[0]['time']

        # Only enable gaze data present in the recording
        for eye_pos in list(self._gaze.keys()):
            self._gaze[eye_pos]['data'] = False
        if 'gaze_posX' in HEADER and 'gaze_dirX' in HEADER:
            self._gaze['']['data'] = True
        if 'gazeL_posX' in HEADER and 'gazeL_dirX' in HEADER:
            self._gaze['L']['data'] = True
        if 'gazeR_posX' in HEADER and 'gazeR_dirX' in HEADER:
            self._gaze['R']['data'] = True

        # Find tracked nodes
        _nodes_builtin = ['gaze', 'gazeL', 'gazeR', 'tracker', 'trackerL', 'trackerR']
        for field in HEADER:
            if field[-5:] == '_posX' and field[0:-5] not in _nodes_builtin:
                self.replay_nodes.append(field[0:-5])
        self._update_nodes()
        self._set_ui()
        print('* Loaded {:d} replay samples from {:s}.'.format(len(s), sample_file))
        if len(self.replay_nodes) > 1:
            print('* Replay contains {:d} tracked nodes: {:s}.'.format(len(self.replay_nodes), ', '.join(self.replay_nodes)))


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
            print('Replay started.')
            self._set_ui()

        
    def stopReplay(self):
        """ Stop an ongoing replay """
        if self.replaying:
            if self._player is not None:
                self._player.setEnabled(False)
            self.replaying = False
            print('Replay stopped at frame {:d}.'.format(self._frame))
            self._set_ui()


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
        for eye_pos in list(self._gaze.keys()):
            if self._gaze[eye_pos]['node'] is not None:
                if self._gaze[eye_pos]['data']:
                    node = self._gaze[eye_pos][self._gaze[eye_pos]['node']]
                    eye_mat = viz.Matrix()
                    eye_mat.setEuler([f['gaze{:s}_dirX'.format(eye_pos)],
                                    f['gaze{:s}_dirY'.format(eye_pos)],
                                    f['gaze{:s}_dirZ'.format(eye_pos)]])
                    eye_mat.setPosition([f['gaze{:s}_posX'.format(eye_pos)],
                                        f['gaze{:s}_posY'.format(eye_pos)],
                                        f['gaze{:s}_posZ'.format(eye_pos)]])
                    eye_mat.setScale(node.getScale())
                    node.setMatrix(eye_mat)
                    node.visible(True)
                else:
                   self._gaze[eye_pos][self._gaze[eye_pos]['node']].visible(False) 

        # Position the 3D gaze cursor and other nodes
        for node in self._nodes.keys():
            if self._nodes[node]['visible']:
                self._nodes[node]['obj'].setPosition([f['{:s}_posX'.format(node)], f['{:s}_posY'.format(node)], f['{:s}_posZ'.format(node)]])

        if self.replay_view:
            viz.MainView.setEuler([f['view_dirX'], f['view_dirY'], f['view_dirZ']])
            viz.MainView.setPosition([f['view_posX'], f['view_posY'], f['view_posZ']])

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


    def setMainViewReplay(self, enabled=True):
        """ Controls whether the replay viewport will move with 
        recorded position and orientation data. 

        Args:
            enabled (bool): if True, move MainView with replay data """
        self.replay_view = enabled

