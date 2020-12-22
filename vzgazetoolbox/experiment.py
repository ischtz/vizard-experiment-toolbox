# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Experiment framework classes

import sys
import random

if sys.version_info[0] == 3:
    from time import perf_counter
else:
    from time import clock as perf_counter	

import viz

from .data import ParamSet

STATE_NEW = 0
STATE_STARTED = 10
STATE_DONE = 20



class Trial(object):

    def __init__(self, params=None, index=-1, block=None):
        """ Contains data of a single experimental trial, keeps 
        track of start and end times, data recorders etc.

        Args:
            params (dict): Initial parameters to assign for this trial
            index (int): Assigned by Experiment to keep track of current index
            block (int): Presentation block this trial belongs to
        """
        self._start_time = None
        self._start_tick = None
        self._end_time = None
        self._end_tick = None

        self._index = index
        self._state = STATE_NEW

        self.block = block

        # Trial results, to be set by Vizard script
        self.results = ParamSet()

        # Parameters, set directly or imported from file
        if params is None:
            self.params = ParamSet()
        else:
            self.params = ParamSet(input_dict=params)


    def __repr__(self):
        blockstr = ''
        if self.block is not None:
            blockstr = ', block {:d}'.format(int(self.block))
        if self._state == STATE_NEW:
            statestr = ', never run'
        elif self._state == STATE_STARTED:
            statestr = ', started'
        elif self._state == STATE_DONE:
            statestr = ', done'
        s = '<Trial (index {:d}{:s}{:s})\n'.format(int(self._index), blockstr, statestr)
        s += 'params: {:s}\n'.format(repr(self.params))
        s += 'results: {:s}>\n'.format(repr(self.results))
        return s


    def _start(self, index=0):
        """ Record trial start time """
        self._index = index
        self._start_tick = viz.tick()
        self._start_time = perf_counter() * 1000.0
        self._state = STATE_STARTED


    def _end(self):
        """ Record trial start time """
        self._end_tick = viz.tick()
        self._end_time = perf_counter() * 1000.0
        self._state = STATE_DONE


    @property
    def index(self):
        """ Return current trial index at runtime """
        return self._index


    @property
    def number(self):
        """ Return current trial number at runtime """
        return self._index + 1


    @property
    def running(self):
        """ returns True if this trial is currently running """
        return self._state == STATE_STARTED


    @property
    def done(self):
        """ returns True if this trial was run """
        return self._state >= STATE_DONE


    @property
    def starttime(self):
        """ Return Vizard time stamp of when this trial was started """
        if self._state < STATE_STARTED:
            e = 'Trying to access start time of a trial that has not been started yet!'
            raise RuntimeError(e)
        else:
            return self._start_tick


    @property
    def endtime(self):
        """ Return Vizard time stamp of when this trial ended """
        if self._state < STATE_DONE:
            e = 'Trying to access end time of a trial that has not been finished!'
            raise RuntimeError(e)
        else:
            return self._end_tick
