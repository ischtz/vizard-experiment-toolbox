# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Experiment framework classes

import os
import sys
import csv
import copy
import time
import random

if sys.version_info[0] == 3:
    from time import perf_counter
else:
    from time import clock as perf_counter	

import viz
import vizinput

from .data import ParamSet

STATE_NEW = 0
STATE_RUNNING = 10
STATE_DONE = 20


class Experiment(object):
    
    def __init__(self, name=None, trial_file=None, config=None, debug=False):
        """ Class to hold an entire VFX experiment. Manages trials, data recording, 
        and timing. 

        Args:
            name (str): Experiment name (label, used e.g. in file names)
            trial_file (str): Optional file name of initial trial parameter file
            config (dict): Optional initial config parameters
            debug (bool): it True, print additional debug output
        """
        if name is None:
            print('Note: Experiment name is not set, using "Experiment1". You can specify the name='' argument when creating an Experiment() object.')
            self.name = 'Experiment1'
        else:
            self.name = name

        self.trials = []
        self._blocks = []
        self._block_trials = {}

        if config is not None:
            if type(config) == str:
                try:
                    self.config = ParamSet.fromJSONFile(config)
                except ValueError:
                    raise ValueError('Passed config file must be a valid JSON file!')
            else:
                self.config = ParamSet(input_dict=config)
        else:
            self.config = ParamSet()

        self._state = STATE_NEW
        self._cur_trial = 0
        self._trial_running = False
        self.debug = debug
        self._base_filename = None
        
        if trial_file is not None:
            self.addTrialsFromCSV(trial_file)


    def _dlog(self, text):
        """ Log debug information to console if debug output is enabled 
        
        Args:
            String to print
        """
        if self.debug:
            print('[{:s}] {:.4f} - {:s}'.format('exp', viz.tick(), text))


    @property
    def output_file_name(self):
        """ Base file name for output files, including date and time 
        and participant metadata if available. Generated and cached on 
        first access. """
        if self._base_filename is None:                
            fn = self.name
            fn += '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime())
            self._base_filename = fn
        return self._base_filename

    
    def addTrials(self, num_trials=1, params={}, block=None):
        """ Add a specified number of trials. The contents of
        the 'params' dict are copied to each trial. You can then further
        modify each trial individually using its 'params' attribute.

        Args:
            num_trials (int): Number of trials to create
            params (dict): Parameter values to set in all trials
            block (int): Optional block number to group trials into blocks
        """
        if block is None:
            block = 0
        for t in range(0, num_trials):
            self.trials.append(Trial(params=params, index=t, block=block))
        self._updateBlocks()
        self._dlog('Adding {:d} trials: {:s}'.format(num_trials, str(params)))


    def addTrialsFromCSV(self, file_name=None, sep='\t', block=None, block_col=None):
        """ Read a list of trials from a CSV file, adding the columns
        as parameter values to each trial (one trial per row). If no file is 
        specified, show Vizard file selection dialog.

        Args:
            file_name (str): name of CSV file to read, or None to show selection dialog
            sep (str): column separator
            block (int): Block number to assign to trials (overrides block_col)
            block_col (str): Column name to use for block numbering
        """
        if file_name is None:
            # Show file dialog and pick a reasonable default for the separator
            file_name = vizinput.fileOpen(filter=[('Trial files', '*.csv;*.tsv;*.dat;*.txt')])
            ext = os.path.splitext(file_name)[1]
            if ext.upper() in ['.CSV', '.DAT']:
                sep=';'

        trial_no = 0
        with open(file_name, 'r') as tf:
            reader = csv.DictReader(tf, delimiter=sep)
            for row in reader:
                params = {}
                for h in reader.fieldnames:

                    # Convert numeric values
                    data = row[h]
                    try:
                        params[h] = int(data)
                    except ValueError:
                        try:
                            params[h] = float(data)
                        except ValueError:
                            params[h] = data

                if block is None:
                    if block_col is not None:
                        # Use column if no block number specified
                        if block_col not in params.keys():
                            s = 'addTrialsFromCSV: Block variable "{:s}" not found in input file!'
                            raise ValueError(s.format(block_col))
                        else:
                            bl = int(params[block_col])

                    elif block_col is None:
                        # Nothing specified, use default (0)
                        bl = 0
                else:
                    # Use block argument if present (overrides column)
                    bl = int(block)

                self.trials.append(Trial(params=params, index=trial_no, block=bl))
                trial_no += 1

        self._updateBlocks()

        if '_trial_input_files' not in self.config:
            self.config['_trial_input_files'] = []
        self.config['_trial_input_files'].append(file_name)
        self._dlog('Adding {:d} trials from file: {:s}'.format(trial_no, file_name))


    def clearTrials(self):
        """ Remove all current trials from the experiment """
        self.trials = []
        self._updateBlocks()
        self._dlog('Trials cleared.')

    
    def randomizeTrials(self, across_blocks=False):
        """ Shuffle trial order globally or within blocks 
        
        Args:
            across_blocks (bool): if True, shuffle all trials 
                irrespective of their block number
        """
        if self._state == STATE_RUNNING:
            raise ValueError('Cannot randomize trials while experiment is in progress!')
        else:
            self._updateBlocks()
            if self.trials is not None:
                if across_blocks:
                    random.shuffle(self.trials)
                    self._dlog('Trials randomized across blocks.')
                else:
                    shuffled_trials = []
                    for block in copy.deepcopy(self._blocks):
                        btrials = self._block_trials[block]
                        random.shuffle(btrials)
                        shuffled_trials.extend(btrials)
                    self.trials = shuffled_trials
                    self._dlog('Trials randomized.')
    

    def _updateBlocks(self):
        """ Rebuild experiment list of blocks and corresponding trials """
        self._blocks = []
        self._block_trials = {}

        if self.trials is not None and len(self.trials) > 0:
            for t in self.trials:
                if t.block not in self._blocks:
                    self._blocks.append(t.block)
                if t.block not in self._block_trials.keys():
                    self._block_trials[t.block] = []
                self._block_trials[t.block].append(t)
            self._blocks.sort()
    

    def __repr__(self):
        s = '<Experiment, {:d} trials'
        if len(self._blocks) > 0:
            s += ', {:d} block(s) {:s}'.format(len(self._blocks), str(self._blocks))
        s += '>'
        return s.format(len(self.trials))


    def __len__(self):
        """ Return 'length' of Experiment, i.e., number of trials """
        return len(self.trials)


    def __iter__(self):
        return iter(self.trials)


    @property
    def running(self):
        """ returns True if experiment is currently running """
        return self._state == STATE_RUNNING


    @property
    def done(self):
        """ returns True if all trials have been run """
        return self._state >= STATE_DONE


    @property
    def blocks(self):
        """ List of trial blocks in this experiment """
        self._updateBlocks()
        return copy.deepcopy(self._blocks)


    @property
    def currentTrial(self):
        """ Return the current trial object if experiment is running """
        if self._trial_running:
            return self.trials[self._cur_trial]
        else:
            raise RuntimeError('Tried to access the current trial while no trial was running')


    @property
    def currentTrialNumber(self):
        """ Return the current trial number if experiment is running """
        if self._trial_running:
            return self._cur_trial
        else:
            raise RuntimeError('Tried to access the current trial while no trial was running')


    def startNextTrial(self, print_summary=True):
        """ Start the next trial in the trial list, if any 
        
        Args:
            print_summary (bool): if True, print out trial status and parameters
        """
        if self._trial_running:
            raise RuntimeError('Cannot start a trial while another trial is in progress!')

        if self._cur_trial == 0 and not self.trials[self._cur_trial].done:
            trial_idx = 0   # first trial

        elif self._cur_trial + 1 >= len(self.trials):
            self._state == STATE_DONE
            raise RuntimeError('No further trials remaining in trial list.')

        else:
            trial_idx = self._cur_trial + 1

        self.startTrial(trial_idx=trial_idx, print_summary=print_summary)

    
    def startTrial(self, trial_idx, repeat=False, print_summary=True):
        """ Start a specific trial by its index in the trial list,
        e.g. the first trial is experiment.trials[0]. By default each 
        trial is only run once unless repeat is set to True.

        Args:
            trial_idx: Trial object or index of trial to run
            repeat (bool): if True, allow repetition of an already finished trial
            print_summary (bool): if True, print out trial status and parameters
        """
        if self._trial_running:
            raise RuntimeError('Cannot start a trial while another trial is in progress!')

        if type(trial_idx) == Trial:
            trial_idx = trial_idx.index

        if self.trials[trial_idx].done and not repeat:
            s = 'Trial {:d} has already been run, set repeat=True to force repeat!'.format(trial_idx)
            raise RuntimeError(s)

        self._cur_trial = trial_idx
        if self._state < STATE_RUNNING:
            self._state = STATE_RUNNING
        self.trials[trial_idx]._start(index=trial_idx)
        self._trial_running = True



    def endCurrentTrial(self, print_summary=True):
        """ End the currently running trial 
        
        Args:
            print_summary (bool): if True, print out summary of trial results
        """
        if not self._trial_running:
            raise RuntimeError('There is no running trial to be ended!')

        self.trials[self._cur_trial]._end()
        if self._cur_trial + 1 >= len(self.trials):
            # Stop experiment if this was the last trial
            self._state = STATE_DONE
        self._dlog('Ended trial {:d}'.format(self._cur_trial))
        self._trial_running = False

        if print_summary:
            print(self.trials[self._cur_trial].summary)
        else:
            self._dlog(self.trials[self._cur_trial].summary)


    def saveTrialData(self, file_name=None, sep='\t'):
        """ Shortcut to saveTrialDataToCSV 
        
        Args:
            file_name (str): Name of CSV file to write to
            sep (str): Field separator string (default: Tab)
        """
        if file_name is None:
            file_name = self._generateFileName('tsv')
        self.saveTrialDataToCSV(file_name, sep)


    def saveTrialDataToCSV(self, file_name=None, sep='\t'):
        """ Saves trial parameters and results to CSV file

        Args:
            file_name (str): Name of CSV file to write to
            sep (str): Field separator string (default: Tab)
        """
        if file_name is None:
            file_name = self._generateFileName('tsv')

        all_keys = []
        tdicts = []
        for t in self.trials:
            td = dict(t.params)
            td.update(dict(t.results))
            td['_start_tick'] = t._start_tick
            td['_end_tick'] = t._end_tick
            td['_start_time'] = t._start_time
            td['_end_time'] = t._end_time
            td['_original_idx'] = t._index
            
            # Collect superset of all param and result keys
            for key in list(td.keys()):
                if key not in all_keys:
                    all_keys.append(key)
            tdicts.append(td)

        all_keys.sort()
        with open(file_name, 'w') as of:
            writer = csv.DictWriter(of, delimiter=sep, lineterminator='\n', 
                                    fieldnames=all_keys)
            writer.writeheader()
            for td in tdicts:
                writer.writerow(td)


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
        elif self._state == STATE_RUNNING:
            statestr = ', started'
        elif self._state == STATE_DONE:
            statestr = ', done'
        s = '<Trial (index {:d}{:s}{:s})\n'.format(int(self._index), blockstr, statestr)
        s += 'params: {:s}\n'.format(repr(self.params))
        s += 'results: {:s}>\n'.format(repr(self.results))
        return s


    def _start(self, index):
        """ Record trial start time """
        self._index = index
        self._start_tick = viz.tick()
        self._start_time = perf_counter() * 1000.0
        self._state = STATE_RUNNING


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
        return self._state == STATE_RUNNING


    @property
    def done(self):
        """ returns True if this trial was run """
        return self._state >= STATE_DONE


    @property
    def status(self):
        """ String description of current trial status """
        states = {STATE_NEW: 'not run',
                  STATE_RUNNING: 'running',
                  STATE_DONE: 'done'}
        return states[self._state]


    @property
    def summary(self):
        """ Trial summary string. Includes params for a running trial and 
        results for a finished trial.
        """
        value_str = ''
        if self.status == 'running' and len(self.params) > 0:
            value_str = 'Params: ' + ', '.join(['{:s}={:s}'.format(l, str(res)) for (l, res) in self.params])
        elif self.status == 'done' and len(self.results) > 0:
            value_str = 'Results: ' + ', '.join(['{:s}={:s}'.format(l, str(res)) for (l, res) in self.results])
        s = 'Trial #{: 3d} {:s}. {:s}'.format(self.number, self.status, value_str)
        return s


    @property
    def starttime(self):
        """ Return Vizard time stamp of when this trial was started """
        if self._state < STATE_RUNNING:
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

