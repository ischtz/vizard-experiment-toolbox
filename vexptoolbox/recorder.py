# -*- coding: utf-8 -*-

# vexptoolbox: Vizard Toolbox for Behavioral Experiments
# Gaze and object tracking and recording class

import sys
import csv
import time
import math
import copy 
import random 
import pickle

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

VALIDATION_START_EVENT = viz.getEventID('EyeTrackerValidationStart')
VALIDATION_END_EVENT = viz.getEventID('EyeTrackerValidationEnd')
RECORDING_START_EVENT = viz.getEventID('RecordingStartEvent')
RECORDING_END_EVENT = viz.getEventID('RecordingEndEvent')


class SampleRecorder(object):

    def __init__(self, eye_tracker=None, tracked_nodes=None, DEBUG=False, missing_val=-99999.0,
                 cursor=False, key_calibrate='c', key_preview='p', key_validate='v',
                 targets=VAL_TAR_CR10, prealloc=324000, priority=viz.PRIORITY_PLUGINS+1,
                 tracked_nodes_rf=viz.ABS_GLOBAL):
        """ Eye movement recording and accuracy/precision measurement class.

        Args:
            eye_tracker: Vizard extension sensor object representing an eye tracker
            tracked_nodes (dict): Dict of extra nodes to track, as {'node label': node3d_object} 
            DEBUG (bool): if True, print debug output to console and store extra fields
            missing_val (float): Value to log for missing data
            cursor (bool): if True, show cursor at current 3d gaze position
            key_calibrate (str): Vizard key code that should trigger eye tracker calibration
            key_preview (str): Vizard key code that should trigger target preview
            key_validate (str): Vizard key code that should trigger gaze validation
            targets: default validation target set to use (see validateEyeTracker())
            prealloc (int): number of samples to preallocate to avoid skipped frames due to 
                Python list extension. Default should be good for 60 min at 90 Hz.
            priority: Vizard priority value to apply to sample collection task
            tracked_nodes_rf: Reference frame for tracked nodes, default: viz.ABS_GLOBAL
        """
        self.debug = DEBUG
        self.priority = priority

        # Eye tracker properties
        self._tracker = None
        self._tracker_type = None
        self._tracker_has_eye_flag = False
        if eye_tracker is not None:
            self.addEyeTracker(eye_tracker)

        # Additional tracked Vizard nodes
        self._tracked_nodes = {}
        if tracked_nodes is not None and type(tracked_nodes) == dict:
            for label in list(tracked_nodes.keys()):
                self.addTrackedNode(node=tracked_nodes[label], label=label)
        self._tracked_nodes_rf = tracked_nodes_rf

        # Value for missing data, since we can't use np.nan
        self.MISSING = missing_val

        # Latest gaze data
        self._gazemat = viz.Matrix()
        self._gazematL = viz.Matrix()
        self._gazematR = viz.Matrix()
        self._gaze3d = [self.MISSING, self.MISSING, self.MISSING]
        self._gaze3d_valid = False
        self._gaze3d_intersect = None
        self._gaze3d_intersect_name = ''
        self._gaze3d_last_valid = None

        # Sample recording task
        self.recording = False
        self._force_update = False
        self._samples = [None,] * prealloc
        self._samples_idx = 0
        self._prealloc = prealloc
        self._val_samples = []
        self._events = []
        self._customvars = ParamSet()
        self._recorder = vizact.onupdate(self.priority, self._onUpdate)

        # Gaze validation
        self._scene = viz.addScene()
        self.fix_size = 0.5 # radius in degrees
        self.tar_plane_color = [0.4, 0.4, 0.4]
        self._validation_results = []
        self._default_targets = targets
        
        # Gaze cursor
        self._cursor = vizshape.addSphere(radius=0.05, color=[1.0, 0.0, 0.0])
        self._cursor.disable(viz.INTERSECTION)
        self.showGazeCursor(cursor)

        # Register task callbacks for interactive keys
        if key_calibrate is not None:
            self._cal_callback = vizact.onkeydown(key_calibrate, viztask.schedule, self.calibrateEyeTracker)
            self._dlog('Key callback registered: Calibration ({:s}).'.format(key_calibrate))
        if key_validate is not None:
            self._val_callback = vizact.onkeydown(key_validate, viztask.schedule, self.validateEyeTracker)
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
            print('[{:s}] {:.4f} - {:s}'.format('REC', viz.tick(), str(text)))
            

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
        
    
    def addEyeTracker(self, eye_tracker, replace=False):
        """ Sets the eye tracking device to record samples from.
        
        Args:
            eye_tracker: Vizard sensor or linked node representing eye tracker
            replace (bool): if True, permit changing of the eye tracer at runtime
        """
        if self._tracker is not None and not replace:
            err = 'Adding more than one eye tracker is not supported. ' 
            err += 'Set replace=True to switch devices.'
            raise RuntimeError(err)

        self._tracker = eye_tracker
        self._tracker_type = type(eye_tracker).__name__
        if self._tracker_type in ['ViveProEyeTracker']:
            # Trackers supporting monocular data via the sensor flag parameter
            self._tracker_has_eye_flag = True
        self._dlog('Added eye tracker: {:s}.'.format(self._tracker_type))


    def addTrackedNode(self, node, label):
        """ Specify a Vizard.Node3d whose position and orientation should be
        logged on each display frame. Ensure this node is not deleted after
        adding it to the recorder object!

        Args:
            node: any Vizard Node3D object
            label (str): Label for this node in log files
        """
        reserved = ['view', 'tracker', 'gaze', 'gaze3d', 'pupil'] + list(self._tracked_nodes.keys())
        if label.lower() in reserved:
            raise ValueError('Tracked node label "{:s}" exists! Please choose a different label.'.format(label))
        self._tracked_nodes[label] = node
        self._dlog('Added tracked node: {:s} (ID: {:d}).'.format(label, node.id))


    def getCurrentGazePoint(self):
        """ Returns the current 3d gaze point if gaze intersects with the scene. """
        return self._gaze3d


    def getCurrentGazeMatrix(self, eye=viz.BOTH_EYE):
        """ Returns the current gaze direction transform matrix 
        
        Args:
            eye (int): Eye to return gaze matrix for, e.g. viz.LEFT_EYE
        """
        err = 'The eye= argument requires monocular gaze data, which is not available for the current eye tracker.'
        if eye is not None:
            if eye == viz.LEFT_EYE:
                if not self._tracker_has_eye_flag:
                    return NotImplementedError(err)
                else:
                    return self._gazematL

            elif eye == viz.RIGHT_EYE:
                if not self._tracker_has_eye_flag:
                    return NotImplementedError(err)
                else:
                    return self._gazematR

        return self._gazemat


    def getCurrentGazeTarget(self):
        """ Returns the currently fixated node if a valid intersection is found """
        return self._gaze3d_intersect


    def getLastValidGazeTarget(self):
        """ Returns the node that last received a valid gaze intersection """
        return self._gaze3d_last_valid


    def waitGazeNearTarget(self, target, tolerance=2.0):
        """ Wait until gaze is on (or close to) a target position 
        
        Args:
            target (3-tuple): target position (X, Y, Z) in world space
            tolerance (float): Gaze error tolerance in degrees
        """
        gaze_err = 9999
        while gaze_err >= tolerance:
            eyeTarVec = vizmat.VectorToPoint(self._gazemat.getPosition(), target)
            eyeGazeVec = self._gazemat.getForward()
            gaze_err = vizmat.AngleBetweenVector(eyeGazeVec, eyeTarVec) 
            yield viztask.waitTime(0.008)


    def waitGazeDwell(self, objects, dwell=0.5):
        """ Wait until one out of multiple objects is fixated for a 
        certain amount of time, return the fixated (selected) node 

        Args:
            objects: list of nodes, or dict with nodes as values
            dwell (float): Selection dwell time in seconds
        """
        if type(objects) == dict:
            o = {obj.id: obj for obj in objects.values()}
        else:
            o = {obj.id: obj for obj in objects}
        d = {id: 0.0 for id in o.keys()}

        while True:
            dt = viz.getFrameElapsed()
            if self._gaze3d_valid:
                for id in o.keys():
                    if self._gaze3d_intersect == o[id]:
                        d[id] += dt
                    else:
                        # Reset dwell for all non-fixated targets
                        d[id] = 0.0

            yield viztask.waitTime(0.008)
            
            for id in d.keys():
                if d[id] >= dwell:
                    viztask.returnValue(o[id])

    
    def waitGazeSelectionFeedback(self, objects, dwell=0.5, highlight_color=None, 
                                  select_color=None, feedback_dur=0.5):
        """ Wait until one out of multiple objects is selected by
        fixating for a given dwell time. Highlights the currently fixated
        object and gives visual feedback of selection.
        
        Args:
            objects: list of nodes, or dict with nodes as values
            dwell (float): Selection dwell time in seconds
            highlight_color (3-tuple): Emissive color to indicate current object
            select_color (3-tuple): Color to set the selected object to
            feedback_dur (float): Duration of color feedback in seconds
        """
        if type(objects) == dict:
            o = {obj.id: obj for obj in objects.values()}
        else:
            o = {obj.id: obj for obj in objects}
        d = {id: 0.0 for id in o.keys()}
        h = {id: o[id].getEmissive() for id in o.keys()}
        c = {id: o[id].getColor() for id in o.keys()}

        while True:
            last_id = -1
            dt = viz.getFrameElapsed()
            if self._gaze3d_valid:
                for id in o.keys():
                    if self._gaze3d_intersect == o[id]:
                        d[id] += dt
                        last_id = id
                    else:
                        d[id] = 0.0 # reset dwell

            if highlight_color is not None:
                for id in o.keys():
                    if id == last_id:
                        o[id].emissive(highlight_color)
                    else:
                        o[id].emissive(h[id])

            yield viztask.waitTime(0.008)
            
            for id in d.keys():
                o[id].emissive(h[id]) # make sure to reset all highlights
                if d[id] >= dwell:
                    
                    if select_color is not None and feedback_dur > 0:
                        o[id].color(select_color)
                        yield viztask.waitTime(feedback_dur)
                        o[id].color(c[id])
                    viztask.returnValue(o[id])


    def waitNodeNearTarget(self, node, pos, distance=0.05):
        """ Wait until the given node is near a specific world coordinate
        with a given distance threshold (e.g., controller near starting position).
        For more complex behavior, consider using the vizproximity module.

        Args:
            node: The Vizard node or sensor object to track
            pos (3-tuple): 3D coordinate in world space
            distance (float): Minimal distance to trigger position
        """
        d = 99999
        while d >= distance:
            p = node.getPosition(viz.ABS_GLOBAL)
            d = vizmat.Distance(p, pos)
            if d < distance:
                return
            yield viztask.waitTime(0.008)

    
    def waitObserverPosition(self, pos, radius=0.2):
        """ Wait until the observer (MainView) is above a certain floor position
        within a given radius, e.g. if participants should walk to a specific
        location in the virtual environment. 
        For more complex behavior, consider using the vizproximity module.

        Args:
            pos (2-tuple): X-Z coordinate in world space (if a 3-tuple is given, 
                the Y value is ignored)
            radius (float): Minimal distance to trigger position
        """
        d = 99999
        if len(pos) == 2:
            pos = [pos[0], 0, pos[2]]
        while d >= radius:
            p = viz.MainView.getPosition(viz.ABS_GLOBAL)
            d = vizmat.Distance([p[0], 0, p[2]], 
                                [pos[0], 0, p[2]])
            if d < radius:
                return
            yield viztask.waitTime(0.008)


    def showGazeCursor(self, visible):
        """ Set visibility of the gaze cursor node """
        self._cursor.visible(visible)


    def getValResults(self):
        """ Return results of all eye tracker validations performed as a list """
        return copy.deepcopy(self._validation_results)


    def getLastValResult(self):
        """ Return a copy of the ValidationResult object resulting from the most
        recent gaze validation measurement. """
        if len(self._validation_results) > 0:
            return copy.deepcopy(self._validation_results[-1])
        else:
            return None


    def _getRawRecording(self, clear=True):
        """ Return last recording data as list of dicts """
        sidx = self._samples_idx
        rec_s = copy.copy(self._samples)
        rec_e = copy.copy(self._events)
        if sidx < self._prealloc:
            rec_s = rec_s[0:sidx]
        if clear:
            self.clearRecording(samples=True, events=True)        
        return (rec_s, rec_e)


    def getLastRecording(self, clear=False):
        """ Return last sample recording as a (samples, events) tuple, each with 
        a dictionary of sample data lists for each data stream (i.e., samples.time[0:10]). 

        Args:
            clear (bool): if True, clear data afterwards (also stops recording if active)
        """
        samples = {}
        events = {}

        if self.recording:
            print('getLastRecording(): Recording is still active, data may be incomplete!')

        sidx = self._samples_idx
        rec_s = copy.copy(self._samples)
        rec_e = copy.copy(self._events)
        if sidx < self._prealloc:
            rec_s = rec_s[0:sidx] # cut to size if preallocated

        # Collect all data fields beforehand, so we can set None for missing data
        s_fields = []
        for s in rec_s:
            for key in s.keys():
                if key not in s_fields:
                    s_fields.append(key)
        s_fields = sorted(s_fields)                    
        e_fields = ['time', 'message']

        for f in s_fields:
            if f not in samples.keys():
                samples[f] = []
            for s in rec_s:
                try:
                    samples[f].append(s[f])
                except KeyError:
                    samples[f].append(None)

        for f in e_fields:
            if f not in events.keys():
                events[f] = []
            for e in rec_e:
                try:
                    events[f].append(e[f])
                except KeyError:
                    events[f].append(None)

        if clear:
            self.clearRecording(samples=True, events=True)

        return (samples, events)
        
    
    def setCustomVar(self, variable, value=None):
        """ Set or update a custom variable, logged on each sample.
        Ex.: vizact.onkeydown(viz.KEY_RETURN, rec.setCustomVar, 'key', 1)

        Args:
            variable (str/dict): Name of variable to set or change,
                alternatively: dict with multiple variables to update
            value: Value to store
        """
        if type(variable) == dict:
            self._customvars.__dict__.update(variable)
        else:    
            self._customvars[variable] = value
    

    def getCustomVar(self, variable):
        """  Get current value of a custom recorder variable.

        Args:
            variable (str): Name of variable to set or change
        """
        if variable in self._customvars.keys():
            return self._customvars[variable]
        else:
            raise KeyError('The requested custom variable was never set!')


    @property
    def custom_vars(self):
        return self._customvars

    
    def measureIPD(self, sample_dur=1000.0):
        """ Measure Inter-Pupillary Distance (IPD) of the HMD wearer
        
        Args:
            sample_dur (float): sampling duration in ms

        Returns:
            IPD as a single float value, in mm 
        """
        if self._tracker is None:
            raise RuntimeError('No eye tracker set up, measureIPD() method is not available!')

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
                - Target set from vexptoolbox.VAL_TAR_*, OR
                - List of targets (x, y, depth), x/y in visual degrees, depth in m
            cursor (bool): if True, show gaze cursor during preview
        """
        prev_scene = viz.MainWindow.getScene()
        prev_headlight_state = viz.MainView.getHeadLight().getEnabled()
        viz.MainView.getHeadLight().enable()
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
        if not prev_headlight_state:
            viz.MainView.getHeadLight().disable()
        viz.MainWindow.setScene(prev_scene)
        self._dlog('Original scene returned')


    def calibrateEyeTracker(self):
        """ Calibrates the eye tracker via its calibrate() method """
        if self._tracker is None:
            raise RuntimeError('No eye tracker set up, calibrateEyeTracker() method not available!')

        self._dlog('Starting eye tracker calibration.')
        yield self._tracker.calibrate()
        self._dlog('Eye tracker calibration finished.')    


    def validateEyeTracker(self, targets=None, dur=2000, tar_color=[1.0, 1.0, 1.0], randomize=True, metadata=None):
        """ Measure gaze accuracy and precision for a set of head-locked targets
        in a special validation scene. 
        
        Args:
            targets: One of the following:
                - Target set from vexptoolbox.VAL_TAR_*, OR
                - List of targets (x, y, depth), x/y in visual degrees, depth in m
            dur (int): sampling duration per target, in ms
            tar_color (3-tuple): Target sphere color
            randomize (bool): if True, randomize target order in each validation
            metadata (dict): Dict of participant metadata to include with result
        
        Returns: vexptoolbox.ValidationResult object 
        """
        if self._tracker is None:
            raise RuntimeError('No eye tracker set up, validateEyeTracker() method not available!')

        if targets is None:
            if self._default_targets is not None:
                targets = self._default_targets
            else:
                # Central target drift check (default)
                targets = VAL_TAR_C

        viz.sendEvent(VALIDATION_START_EVENT)

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
        prev_headlight_state = viz.MainView.getHeadLight().getEnabled()
        viz.MainView.getHeadLight().enable()
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

                dC = vizmat.AngleBetweenVector(eyeGazeVec, eyeTarVec)
                sam['targetErr'] = dC

                angularDiff = vizmat.Transform()
                angularDiff.makeVecRotVec(eyeTarVec, eyeGazeVec)
                (dX, dY, _) = angularDiff.getEuler()
                dY = -dY
                sam['targetErr_X'], sam['targetErr_Y'] = dX, dY

                delta.append(dC)
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
                        
                        dCM = vizmat.AngleBetweenVector(eyeGazeVecM, eyeTarVecM)
                        sam['targetErr{:s}'.format(eye)] = dCM

                        angularDiffM = vizmat.Transform()
                        angularDiffM.makeVecRotVec(eyeTarVecM, eyeGazeVecM)
                        (dXM, dYM, _) = angularDiff.getEuler()
                        dYM = -dYM                        
                        sam['targetErr{:s}_X'.format(eye)] = dXM
                        sam['targetErr{:s}_Y'.format(eye)] = dYM

                        deltaM[eyei].append(dCM)
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
        if not prev_headlight_state:
            viz.MainView.getHeadLight().disable()
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

        self._validation_results.append(copy.deepcopy(rv))
        viz.sendEvent(VALIDATION_END_EVENT)
        viztask.returnValue(rv)


    def checkEyeTrackerDrift(self, threshold=1.5, auto_calibrate=True):
        """ Run single-target validation to check for eye tracker drift. 

        Args:
            threshold (float): Accuracy (gaze error) above which drift check is failed
            auto_calibrate (bool): if True, run calibration automatically when failed
        """
        if self._tracker is None:
            raise RuntimeError('No eye tracker set up, checkEyeTrackerDrift() method not available!')
     
        val_res = yield self.validateEyeTracker(targets=VAL_TAR_C, dur=2000, tar_color=[1.0, 1.0, 1.0])
        if val_res.acc > threshold:
            self._dlog('Drift check FAILED, acc = {:.2f}°'.format(val_res.acc))
            if auto_calibrate:
                yield self.calibrateEyeTracker()
        else:
            self._dlog('Drift check PASSED, acc = {:.2f}°'.format(val_res.acc))
        viztask.returnValue(val_res.acc)

    
    def _onUpdate(self):
        """ Task callback that runs on each display frame. Always updates 
        current gaze data properties, triggers sample recording if recording is on.
        """
        if self._force_update:
            viz.update(viz.UPDATE_PLUGINS | viz.UPDATE_LINKS)

        time_ms = viz.tick() * 1000.0		# Vizard time
        frame = viz.getFrameNumber()		# Vizard frame number
        clock = perf_counter() * 1000.0 		# Python system time

        cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
        nodes = {'view': cW}

        if self._tracker is not None:
            # Gaze and view nodes
            gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
            gW = copy.deepcopy(gT)				# Gaze-in-World FoR
            gW.postMult(cW)
            self._gazemat = gW
            nodes['tracker'] = gT
            nodes['gaze'] = gW

            # Monocular data, if available
            if self._tracker_has_eye_flag:
                gTL = self._tracker.getMatrix(flag=viz.LEFT_EYE)
                gTR = self._tracker.getMatrix(flag=viz.RIGHT_EYE)
                gWL = copy.deepcopy(gTL)
                gWR = copy.deepcopy(gTR)
                gWL.postMult(cW)
                gWR.postMult(cW)
                self._gazematL = gWL
                self._gazematR = gWR
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
                self._gaze3d_intersect_name = g3D_test.name
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
                nodes[obj] = self._tracked_nodes[obj].getMatrix(self._tracked_nodes_rf)

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

            cW = viz.MainView.getMatrix()		# Camera-in-World FoR (Head for HMDs)
            nodes = {'view': cW}

            if self._tracker is not None:
                gT = self._tracker.getMatrix()		# Gaze-in-Tracker FoR
                gW = copy.deepcopy(gT)				# Gaze-in-World FoR
                gW.postMult(cW)
                nodes['tracker'] = gT
                nodes['gaze'] = gW

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
                nodes[obj] = self._tracked_nodes[obj].getMatrix(mode=self._tracked_nodes_rf)

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

        if self._tracker is not None:
            # Store 3D gaze point data
            s['gaze3d_posX'] = self._gaze3d[0]
            s['gaze3d_posY'] = self._gaze3d[1]
            s['gaze3d_posZ'] = self._gaze3d[2]
            if self._gaze3d_valid:
                s['gaze3d_valid'] = 1
                s['gaze3d_object_id'] = int(self._gaze3d_intersect.id)
                s['gaze3d_object_name'] = str(self._gaze3d_intersect_name)
            else:
                s['gaze3d_valid'] = 0
                s['gaze3d_object_id'] = -1
                s['gaze3d_object_name'] = ''

            # Device-specific eye tracking data
            if self._tracker_type == 'ViveProEyeTracker':
                s['pupil_size'] = self._tracker.getPupilDiameter(viz.BOTH_EYE)
                s['pupil_sizeL'] = self._tracker.getPupilDiameter(viz.LEFT_EYE)
                s['pupil_sizeR'] = self._tracker.getPupilDiameter(viz.RIGHT_EYE)
                s['eye_state'] = self._tracker.getEyeOpen(viz.BOTH_EYE)
                s['eye_stateL'] = self._tracker.getEyeOpen(viz.LEFT_EYE)
                s['eye_stateR'] = self._tracker.getEyeOpen(viz.RIGHT_EYE)

        # Additional data fields
        s.update(self._customvars)
        
        # Add to preallocated list, or switch to appending if full
        if self._samples_idx < self._prealloc:
            self._samples[self._samples_idx] = s
            self._samples_idx += 1
        else:
            self._samples.append(s)

        if console:
            # Note: printing coordinates will likely slow down rendering a lot! Use for debugging only.
            cWp = nodes['view'].getPosition()
            cWd = nodes['view'].getEuler()
            if self._tracker is not None:
                gWp = nodes['gaze'].getPosition()
                gWd = nodes['gaze'].getEuler()
                pupilDia = self.MISSING
                if 'pupil_size' in s.keys():
                    pupilDia = s['pupil_size']
                outformat = '{:.4f} {:d}\tviewPOS=({:.3f}, {:.3f}, {:.3f}),\tviewDIR=({:.3f}, {:.3f}, {:.3f}),\tgazePOS=({:.3f}, {:.3f}, {:.3f}),\tgazeDIR=({:.3f}, {:.3f}, {:.3f}), p={:.3f}'
                print(outformat.format(s['time'], s['frameno'], cWp[0], cWp[1], cWp[2], cWd[0], cWd[1], cWd[2], gWp[0], gWp[1], gWp[2], gWd[0], gWd[1], gWd[2], pupilDia))
            else:
                outformat = '{:.4f} {:d}\tviewPOS=({:.3f}, {:.3f}, {:.3f}),\tviewDIR=({:.3f}, {:.3f}, {:.3f})'
                print(outformat.format(s['time'], s['frameno'], cWp[0], cWp[1], cWp[2], cWd[0], cWd[1], cWd[2]))


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
        """ Start recording samples on each display frame
        
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
            viz.sendEvent(RECORDING_START_EVENT)


    def stopRecording(self):
        """ Stop sample recording """
        if self.recording:
            self.recording = False
            self.recordEvent('REC_STOP')
            self._dlog('Recording stopped.')
            self._force_update = False
            viz.sendEvent(RECORDING_END_EVENT)


    def saveRecording(self, sample_file=None, event_file=None, clear_samples=True, clear_events=True, 
                      sep='\t', quat=False, meta_cols={}, _data=None, _append=False):
        """ Save current gaze recording to a tab-separated CSV file 
        and clear the current recording by default.
        
        Args:
            sample_file: Name of output file to write gaze samples to
            event_file: Name of output file to write event data to
            clear_samples (bool): if True, clear recorded samples after saving
            clear_events (bool): if True, clear recorded events after saving
            sep (str): Field separator in output file
            quat (bool): if True, also export rotation Quaternions
            meta_cols (dict): Dict of values to add to each sample (e.g., trial number)
            _data: Tuple (samples, events) to save, None for current recording (mostly internal use)
        """
        # Select data to save
        if _data is not None:
            samples, events = _data
        else:
            # Current recording: cut to size if < preallocation limit
            if self._samples_idx < self._prealloc:
                self._samples = self._samples[0:self._samples_idx]
            samples = self._samples
            events = self._events

        if _append:
            writemode = 'a'
        else:
            writemode = 'w'

        # Samples: select keys to be exported and build file format
        fields = ['time', 'systime', 'view_posX', 'view_posY', 'view_posZ', 'view_dirX', 'view_dirY', 'view_dirZ']

        # Eye tracker fields
        if self._tracker is not None:
            fields += ['gaze_posX', 'gaze_posY', 'gaze_posZ', 'gaze_dirX', 'gaze_dirY', 'gaze_dirZ',
                       'gaze3d_valid', 'gaze3d_posX', 'gaze3d_posY', 'gaze3d_posZ', 'gaze3d_object_id', 'gaze3d_object_name']

            # Tracker-specific fields (not always available)
            special = ['gazeL_posX', 'gazeL_posY', 'gazeL_posZ', 'gazeL_dirX', 'gazeL_dirY', 'gazeL_dirZ',
                    'gazeR_posX', 'gazeR_posY', 'gazeR_posZ', 'gazeR_dirX', 'gazeR_dirY', 'gazeR_dirZ',
                    'pupil_size', 'pupil_sizeL', 'pupil_sizeR', 'eye_state', 'eye_stateL', 'eye_stateR']
            for field in special:
                if field in samples[0].keys():
                    fields += [field,]

        # Additional tracked nodes
        for lbl in self._tracked_nodes.keys():
            fields += ['{:s}_posX'.format(lbl), '{:s}_posY'.format(lbl), '{:s}_posZ'.format(lbl), 
                       '{:s}_dirX'.format(lbl), '{:s}_dirY'.format(lbl), '{:s}_dirZ'.format(lbl)]

        # Quaternions (optional)
        if quat:
            fields += ['view_quatX', 'view_quatY', 'view_quatZ', 'view_quatW']
            if self._tracker is not None:
                fields += ['gaze_quatX', 'gaze_quatY', 'gaze_quatZ', 'gaze_quatW']
            for lbl in self._tracked_nodes.keys():
                fields += ['{:s}_quatX'.format(lbl), '{:s}_quatY'.format(lbl), '{:s}_quatZ'.format(lbl), '{:s}_quatW'.format(lbl)]

        if self.debug and self._tracker is not None:
            fields += ['tracker_posX', 'tracker_posY', 'tracker_posZ', 'tracker_dirX', 'tracker_dirY', 'tracker_dirZ']
            if self._tracker_has_eye_flag:
                fields += ['trackerL_posX', 'trackerL_posY', 'trackerL_posZ', 'trackerL_dirX', 'trackerL_dirY', 'trackerL_dirZ',
                           'trackerR_posX', 'trackerR_posY', 'trackerR_posZ', 'trackerR_dirX', 'trackerR_dirY', 'trackerR_dirZ']

            if quat:
                fields += ['tracker_quatX', 'tracker_quatY', 'tracker_quatZ', 'tracker_quatW']
                if self._tracker_has_eye_flag:
                    fields += ['trackerL_quatX', 'trackerL_quatY', 'trackerL_quatZ', 'trackerL_quatW',
                               'trackerR_quatX', 'trackerR_quatY', 'trackerR_quatZ', 'trackerR_quatW']

        evfields = ['time', 'message']

        # Optional metadata
        for sample in samples:
            sample.update(meta_cols)
        fields += list(meta_cols.keys())
        for event in events:
            event.update(meta_cols)
        evfields += list(meta_cols.keys())

        # Custom sample variables
        fields += list(self._customvars.__dict__.keys())

        # Samples
        if sample_file is not None:
            with open(sample_file, writemode) as of:
                writer = csv.DictWriter(of, delimiter=sep, lineterminator='\n', 
                                        fieldnames=fields, extrasaction='ignore')
                if not _append:
                    writer.writeheader()
                for sample in samples:
                    writer.writerow(sample)
            self._dlog('Saved {:d} samples to file: {:s}'.format(len(samples), sample_file))

        # Events
        if event_file is not None:
            with open(event_file, writemode) as ef:
                writer = csv.DictWriter(ef, delimiter=sep, lineterminator='\n', fieldnames=evfields)
                if not _append:
                    writer.writeheader()
                for event in events:
                    writer.writerow(event)
            self._dlog('Saved {:d} events to file: {:s}'.format(len(events), event_file))

        if sample_file is None and event_file is None:
            self._dlog('Neither sample_file nor event_file were specified. No data saved.')
        else:
            if _data is None and (clear_samples or clear_events):
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

