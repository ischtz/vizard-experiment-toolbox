# -*- coding: utf-8 -*-

# Vizard gaze tracking toolbox
# Experiment framework classes

import os
import sys
import csv
import copy
import time
import json
import random
import itertools

if sys.version_info[0] == 3:
    from time import perf_counter
else:
    from time import clock as perf_counter	

import viz
import vizinfo
import viztask
import vizinput

from .data import ParamSet
from .recorder import SampleRecorder

STATE_NEW = 0
STATE_RUNNING = 10
STATE_DONE = 20

EXPERIMENT_START_EVENT = viz.getEventID('ExperimentStart')
EXPERIMENT_END_EVENT = viz.getEventID('ExperimentStart')
TRIAL_START_EVENT = viz.getEventID('TrialStart')
TRIAL_END_EVENT = viz.getEventID('TrialEnd')


class Experiment(object):
    
    def __init__(self, name=None, trial_file=None, config=None, debug=False, output_file=None, auto_save=True):
        """ Class to hold an entire VFX experiment. Manages trials, data recording, 
        and timing. 

        Args:
            name (str): Experiment name (label, used e.g. in file names)
            trial_file (str): Optional file name of initial trial parameter file
            config (dict): Optional initial config parameters
            debug (bool): it True, print additional debug output
            output_file (str): Base file name (without extension) for output files
            auto_save (bool): if True, automatically save data after each trial
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

        self.participant = ParamSet()

        self._state = STATE_NEW
        self._cur_trial = 0
        self._trial_running = False
        self.debug = debug
        self._base_filename = output_file
        self._auto_save = auto_save
        
        self._recorder = None
        self._auto_record = True

        if trial_file is not None:
            self.addTrialsFromCSV(trial_file)


    def _dlog(self, text):
        """ Log debug information to console if debug output is enabled 
        
        Args:
            String to print
        """
        if self.debug:
            print('[{:s}] {:.4f} - {:s}'.format('EXP', viz.tick(), str(text)))


    @property
    def output_file_name(self):
        """ Base file name for output files, including date and time 
        and participant metadata if available. Generated and cached on 
        first access. """
        if self._base_filename is None:
            fn = self.name
            if 'id' in self.participant:
                fn += '_' + str(self.participant.id)
            if 'session' in self.participant:
                fn += '_' + str(self.participant.session)
            fn += '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime())
            self._base_filename = fn
        return self._base_filename

    
    def addTrials(self, num_trials=1, params={}, list_params={}, block=None):
        """ Add a specified number of trials. The contents of
        the 'params' dict are copied to each trial. You can then further
        modify each trial individually using its 'params' attribute.

        Args:
            num_trials (int): Number of trials to create
            params (dict): Parameter values to set in all trials
            list_params (dict): Parameters to assign to individual trials
                (each dict entry must contain a list of <num_trials> entries)
            block (int): Optional block number to group trials into blocks
        """
        if block is None:
            block = 0

        for key in list_params.keys():
            if len(list_params[key]) != num_trials:
                estr = 'Values in list_params must have the same length as num_trials! [{:s}]'
                raise ValueError(estr.format(key))

        for t in range(0, num_trials):
            tparams = copy.copy(params)
            tparams.update({key:val[t] for key, val in list_params.iteritems()})
            self.trials.append(Trial(params=tparams, block=block))

        self._updateTrialIndices()
        self._updateBlocks()
        self._dlog('Adding {:d} trials: {:s}'.format(num_trials, str(params)))


    def addTrialsFullFactorial(self, levels, repeat=1, params={}, block=None):
        """ Add trials by building a full-factorial experimental design.

        When given as number of levels, generates a numeric range starting
        at 1. Factors are included as params, together with the contents of 
        the params= attribute. 

        Args:
            levels (dict): Factor names (as keys) and values as:
                - number of factor levels (int), e.g. {'condition': 2}, or
                - iterable of factor labels, e.g., {'condition': ['baseline', 'test']}
            repeat (int): Number of times to repeat the full design
            params (dict): Additional parameter values to set in all trials
            block (int): Optional block number to group trials into blocks
        """
        iters = {}
        factors = []
        variables = list(levels.keys())

        for key in variables:
            if type(levels[key]) == int:
                # Number of levels given - generate list
                iters[key] = list(range(1, int(levels[key]) + 1))
            else:
                # Use iterable of labels directly
                iters[key] = levels[key]
            factors.append(iters[key])

        design = list(itertools.product(*factors)) * repeat
        for ix, entry in enumerate(design):
            tparams = {}
            for var, lev in zip(variables, entry):
                tparams[var] = lev
            tparams.update(params)
            self.trials.append(Trial(params=tparams, block=block))
        
        self._updateTrialIndices()
        self._updateBlocks()

        # Debug: print design description
        design_str = []
        for key in variables:
            if type(levels[key]) == int:
                design_str.append(str(levels[key]))
            else:
                design_str.append(str(len(levels[key])))
        design_str = 'x'.join(design_str)
        rep_str = ''
        if repeat != 1:
            rep_str = ', {:d} reps'.format(repeat)
        self._dlog('Adding {:d} trials ({:s} design{:s}), params: {:s}'.format(len(design), design_str, rep_str, str(params)))


    def addTrialsFromCSV(self, file_name=None, sep=None, repeat=1, block=None,
                         block_col=None, params={}, num_rows=None):
        """ Read a list of trials from a CSV file, adding the columns
        as parameter values to each trial (one trial per row). If no file is 
        specified, show Vizard file selection dialog.

        Args:
            file_name (str): name of CSV file to read, or None to show selection dialog
            sep (str): column separator (default: tab)
            repeat (int): Number of times to repeat each trial read from the file
            block (int): Block number to assign to trials (overrides block_col)
            block_col (str): Column name to use for block numbering
            params (dict): Parameter values to set in all trials
                (Caution: Will override identically named columns from input file!)
            num_rows (int): How many trials to read (at least 1, default: all)
        """
        if file_name is None:
            file_name = vizinput.fileOpen(filter=[('Trial files', '*.csv;*.tsv;*.dat;*.txt')])

        if sep is None:
            ext = os.path.splitext(file_name)[1]
            if ext.upper() in ['.TSV']:
                sep='\t'
            else:
                sep=';'

        trial_no = 0
        with open(file_name, 'r') as tf:
            reader = csv.DictReader(tf, delimiter=sep)
            if len(reader.fieldnames) == 1:
                m = 'Warning: Only a single column read from trial file. Is the field separator set correctly (e.g., sep=";")?\n'
                print(m)

            for row in reader:
                cparams = {}
                for h in reader.fieldnames:

                    # Convert numeric values
                    data = row[h]
                    try:
                        cparams[h] = int(data)
                    except ValueError:
                        try:
                            cparams[h] = float(data)
                        except ValueError:
                            cparams[h] = data

                if block is None:
                    if block_col is not None:
                        # Use column if no block number specified
                        if block_col not in cparams.keys():
                            s = 'addTrialsFromCSV: Block variable "{:s}" not found in input file!'
                            raise ValueError(s.format(block_col))
                        else:
                            bl = int(cparams[block_col])

                    elif block_col is None:
                        # Nothing specified, use default (0)
                        bl = 0
                else:
                    # Use block argument if present (overrides column)
                    bl = int(block)

                # Add any other params specified in function call
                cparams.update(params)

                for rep in range(0, repeat):
                    self.trials.append(Trial(params=cparams, block=bl))
                    trial_no += 1

                if num_rows is not None:
                    if trial_no >= num_rows:
                        break

        self._updateTrialIndices()
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
            self._updateTrialIndices()
    

    def requestParticipantData(self, questions={}, session=True, age=True, 
                               gender=True, expname=True):
        """ Show UI to input participant ID and further details. 
        Must be called as a Vizard task (using yield statement)!

        Some common fields are included for standardization, others can
        be added using the questions argument. Participant data is accessible
        through the experiment object's .participant property.

        Args:
            questions (dict or iterable): Further data fields to show
            session (bool): if True, include a session field
            age (bool): if True, include an age field
            gender (bool): if True, include a gender field
            expname (bool): if True, show a field for experiment name
        """
        if type(questions) in (list, tuple):
            questions = {q.replace(' ', ''):q for q in questions}

        ui = vizinfo.InfoPanel('Please enter the following data:', title='Participant Information', 
                               icon=False, align=viz.ALIGN_CENTER_CENTER)
        uid = {}
        if expname:
            uid['__expname__'] = ui.addLabelItem('Experiment', viz.addTextbox())
            uid['__expname__'].message(str(self.name))
        uid['id'] = ui.addLabelItem('Participant ID', viz.addTextbox())
        if session:
            uid['session'] = ui.addLabelItem('Session', viz.addTextbox())
        if age:
            uid['age'] = ui.addLabelItem('Age', viz.addTextbox())
        if gender:
            uid['gender'] = ui.addLabelItem('Gender',viz.addDropList())
            uid['gender'].addItems(['female', 'male', 'non-binary', 'prefer not to say'])

        if len(questions) > 0:
            ui.addSeparator()
            for q in questions.keys():
                uid[q] = ui.addLabelItem(questions[q], viz.addTextbox())

        ui_submit = ui.addItem(viz.addButtonLabel('Save'), align=viz.ALIGN_RIGHT_CENTER)
        yield viztask.waitButtonDown(ui_submit)

        metadata = {}
        for key in uid.keys():
            if key == '__expname__':
                self.name = uid['__expname__'].getMessage()
                continue
            metadata[key] = uid[key].getMessage()
        if gender: 
            metadata['gender'] = uid['gender'].getItems()[uid['gender'].getSelection()]
        
        ui.remove()
        self.participant = ParamSet(metadata)
        self._dlog('Participant Metadata: {:s}'.format(str(metadata)))


    def addSampleRecorder(self, auto_record=True, **kwargs):
        """ Set up sample recorder to record view, gaze, and other
        objects' position and orientation on each display frame. 

        Args:
            auto_record (bool): if True, start and stop recording
                automatically with each trial
            **kwargs: any valid argument to SampleRecorder()
        """
        self._recorder = SampleRecorder(DEBUG=self.debug, **kwargs)
        self._auto_record = auto_record

    
    def addSteamVRDebugOverlay(self, enable=False, hotkey=viz.KEY_F12):
        """ Add a SteamVR debug overlay to the experiment, which can help
        measure positions in a virtual environment, determine controller IDs, 
        etc. Press hotkey to activate (default: F12).
        
        Args:
            enable (bool): Whether the overlay should be visible from the start
            hotkey: Any Vizard key specification, used to show/hide overlay
        """
        try:
            from .steamvr_debug import SteamVRDebugOverlay
            self.debugger = SteamVRDebugOverlay(enable=enable, hotkey=hotkey)
        except: 
            print('Could not add SteamVR debug overlay. Is SteamVR installed and active?')


    def _updateTrialIndices(self):
        """ Set each trial object's index attribute based on the trial list """
        for ix, t in enumerate(self.trials):
            t._index = ix


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
    def recorder(self):
        if self._recorder is not None:
            return self._recorder
        else:
            e = 'Sample recorder needs to be initialized using addSampleRecorder()'
            e += ' before accessing!'
            raise RuntimeError(e)


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
        """ Return the current trial object. If no trial is running, this will
        reference the trial that just ended. """
        return self.trials[self._cur_trial]


    @property
    def currentTrialIndex(self):
        """ Return the current trial index. If no trial is running, this will
        reference the trial that just ended. """
        return self._cur_trial


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
            viz.sendEvent(EXPERIMENT_START_EVENT, self, self.trials[trial_idx])

        self.trials[trial_idx]._start(index=trial_idx)
        self._trial_running = True

        if self._recorder is not None and self._auto_record:
            self._recorder.startRecording()
            self._recorder.recordEvent('TRIAL_START {:d}'.format(trial_idx))

        if print_summary:
            print(self.trials[self._cur_trial].summary)
        else:
            self._dlog(self.trials[self._cur_trial].summary)

        viz.sendEvent(TRIAL_START_EVENT, self, self.trials[trial_idx])


    def endCurrentTrial(self, print_summary=True):
        """ End the currently running trial 
        
        Args:
            print_summary (bool): if True, print out summary of trial results
        """
        if not self._trial_running:
            raise RuntimeError('There is no running trial to be ended!')

        if self._recorder is not None and self._auto_record:
            self._recorder.recordEvent('TRIAL_END {:d}'.format(self.trials[self._cur_trial].index))
            self._recorder.stopRecording()
            sam, ev = self._recorder._getRawRecording(clear=True)
            self.trials[self._cur_trial].samples = sam
            self.trials[self._cur_trial].events = ev

        self.trials[self._cur_trial]._end()
        if self._cur_trial + 1 >= len(self.trials):
            # Stop experiment if this was the last trial
            self._state = STATE_DONE
            viz.sendEvent(EXPERIMENT_END_EVENT, self, self.trials[self._cur_trial])

        self._dlog('Ended trial {:d}'.format(self._cur_trial))
        self._trial_running = False

        if self._auto_save:
            self.saveTrialData('{:s}.tsv'.format(self.output_file_name), rec_data='separate')

        if print_summary:
            print(self.trials[self._cur_trial].summary)
        else:
            self._dlog(self.trials[self._cur_trial].summary)

        viz.sendEvent(TRIAL_END_EVENT, self, self.trials[self._cur_trial])


    def run(self, trial_task, pre_trial_task=None, post_trial_task=None):
        """ Run all trials in current order, executing the trial_task each time
        
        All tasks must accept two arguments: experiment and trial, e.g.
        def TrialTask(experiment, trial):
            yield doSomething

        Args:
            trial_task: Vizard task (containing "yield") to run each trial
            pre_trial_task: Optional task to run before a trial, e.g. to set up stimuli
            post_trial_task: Optional task to run after a trial
        """
        if self._state == STATE_RUNNING:
            raise RuntimeError('The experiment is already running!')
            return
        if len(self.trials) < 1:
            raise RuntimeError('No trials to run!')
            return

        while not self.done:
            self.startNextTrial()

            if pre_trial_task is not None:
                yield pre_trial_task(self, self.currentTrial)
            
            yield trial_task(self, self.currentTrial)

            if post_trial_task is not None:
                yield post_trial_task(self, self.currentTrial)

            self.endCurrentTrial(self.currentTrial)


    def saveTrialData(self, file_name=None, sep='\t', rec_data='single'):
        """ Shortcut to saveTrialDataToCSV 
        
        Args:
            file_name (str): Name of CSV file to write to
            sep (str): Field separator string (default: Tab)
            rec_data: How to save sample and event data if recorded:
                - 'single': One large file with all samples (default)
                - 'separate' Or True: one sample file per trial
                - 'none' or False: Do not save sample data
        """
        if file_name is None:
            file_name = '{:s}.tsv'.format(self.output_file_name)
        self.saveTrialDataToCSV(file_name, sep, rec_data=rec_data)


    def saveTrialDataToCSV(self, file_name=None, sep='\t', rec_data='single'):
        """ Saves trial parameters and results to CSV file

        Args:
            file_name (str): Name of CSV file to write to
            sep (str): Field separator string (default: Tab)
            rec_data: How to save sample and event data if recorded:
                - 'single': One large file with all samples (default)
                - 'separate' Or True: one sample file per trial
                - 'none' or False: Do not save sample data
        """
        if file_name is None:
            file_name = '{:s}.tsv'.format(self.output_file_name)

        if type(rec_data) == bool:
            if rec_data: 
                rec_data = 'single'
            else: 
                rec_data = 'none'

        # Trial data
        self._dlog('Saving trial data...')
        all_keys = []
        tdicts = []
        for t in self.trials:
            td = dict(t.params)
            td.update(dict(t.results))
            td['_trial_index'] = t.index
            td['_trial_number'] = t.number
            td['_start_tick'] = t._start_tick
            td['_end_tick'] = t._end_tick
            td['_start_time'] = t._start_time
            td['_end_time'] = t._end_time

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

        # Sample and event data
        if rec_data.lower() == 'single' and self._recorder is not None:
            file_name_s = '{:s}_samples.tsv'.format(os.path.splitext(file_name)[0])
            file_name_e = '{:s}_events.tsv'.format(os.path.splitext(file_name)[0])

            first = True
            for t in self.trials:
                # Write all trials to same file, but ensure not to append to old data
                if first:
                    self.recorder.saveRecording(sample_file=file_name_s, event_file=file_name_e, _append=False,
                                                _data=(t.samples, t.events), meta_cols={'trial_number': t.number})
                    first = False
                else:
                    self.recorder.saveRecording(sample_file=file_name_s, event_file=file_name_e, _append=True,
                                                _data=(t.samples, t.events), meta_cols={'trial_number': t.number})

        elif rec_data.lower() == 'separate' and self._recorder is not None:
            for t in self.trials:
                try:
                    file_name_s = '{:s}_samples_{:d}.tsv'.format(os.path.splitext(file_name)[0], t.number)
                    file_name_e = '{:s}_events_{:d}.tsv'.format(os.path.splitext(file_name)[0], t.number)
                    if os.path.isfile(file_name_s) and os.path.isfile(file_name_e):
                        continue # This is called on each trial, so skip existing files
                    
                    self.recorder.saveRecording(sample_file=file_name_s, event_file=file_name_e, 
                                                _data=(t.samples, t.events), meta_cols={'trial_number': t.number})
                
                except AttributeError:
                    pass # Skip trials without recorded data


    def toDict(self):
        """ Return all experiment data and results as dict """
        e = {'name': self.name,
             'config': self.config.toDict(),
             'participant': self.participant.toDict()}

        for trial in self.trials:
            if 'trials' not in e.keys():
                e['trials'] = []
            e['trials'].append(trial.toDict())

        if self._recorder is not None:
            if len(self.recorder._validation_results) > 0:
                e['eye_tracker_validations'] = [v.toDict() for v in self.recorder._validation_results]
        return e


    def saveExperimentData(self, json_file=None):
        """ Save all experimental data to JSON file """
        if json_file is None:
            json_file = self.output_file_name + '.json'

        with open(json_file, 'w') as jf:
            jf.write(json.dumps(self.toDict()))
        self._dlog('Saved experiment data to {:s}.'.format(str(json_file)))



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


    def toDict(self):
        """ Return all trial information as a dict """
        d = {'index': self.index, 
             'block': self.block, 
             'status': self.status,
             'times': {'start_time': self._start_time,
                      'start_tick': self._start_tick,
                      'end_time': self._end_time,
                      'end_tick': self._end_tick},
             'params': self.params.toDict(),
             'results': self.results.toDict()}
        if 'samples' in self.__dict__.keys():
            d['samples'] = self.samples
        if 'events' in self.__dict__.keys():
            d['events'] = self.events
        return d


    def toJSON(self):
        """ Return all trial information as JSON """
        return json.dumps(self.toDict())


    def toJSONFile(self, json_file):
        """ Save this trial to a JSON file 

        Args:
            json_file (str): Output file name
        """
        with open(json_file, 'w') as jf:
            jf.write(json.dumps(self.toDict()))
