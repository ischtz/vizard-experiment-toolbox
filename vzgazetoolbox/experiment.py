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


class Trial(object):

    def __init__(self, params=None, index=-1, block=None):

        self._start_time = -1.0
        self._end_time = -1.0
        self._start_tick = -1.0
        self._end_tick = -1.0
        self._index = index

        self.block = block

        # Trial results, to be set by Vizard script
        self.results = ParamSet()

        # Parameters, imported from file
        if params is None:
            self.params = ParamSet()
        else:
            self.params = ParamSet(input_dict=params)


    def __repr__(self):
        s = '<Trial ({:d})\n'.format(int(self._index))
        s += 'params: {:s}\n'.format(repr(self.params))
        s += 'results: {:s}>\n'.format(repr(self.results))
        return s


    def _start(self, index, config):
        """ Record trial start time """
        self._index = index
        self._start_tick = viz.tick()
        self._start_time = perf_counter() * 1000.0
        
        # Allow access to experiment config at run time
        self.config = config
        

    def _end(self):
        """ Record trial start time """
        self._end_tick = viz.tick()
        self._end_time = perf_counter() * 1000.0
        del self.config


    @property
    def index(self):
        """ Return current trial index at runtime """
        return self._index


    @property
    def number(self):
        """ Return current trial number at runtime """
        return self._index + 1