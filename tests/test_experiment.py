import unittest

import os
import time
from tempfile import mkstemp

from vzgazetoolbox.experiment import Trial, Experiment


class TestTrial(unittest.TestCase):

    def test_trial_timing(self):

        t = Trial()

        # New trial has no timing at all
        self.assertIsNone(t._start_tick)
        self.assertIsNone(t._start_time)
        self.assertIsNone(t._end_tick)
        self.assertIsNone(t._end_time)

        # Started trial has start time only
        time.sleep(0.01)
        t._start(0)
        self.assertGreater(t._start_time, 0.0)
        self.assertGreater(t._start_tick, 0.0)
        self.assertIsNone(t._end_tick)
        self.assertIsNone(t._end_time)

        # Finished trial has start and end times
        time.sleep(0.01)
        t._end()
        self.assertGreater(t._start_time, 0.0)
        self.assertGreater(t._start_tick, 0.0)
        self.assertGreater(t._end_time, 0.0)
        self.assertGreater(t._end_tick, 0.0)
        self.assertGreater(t._end_time, t._start_time)
        self.assertGreater(t._end_tick, t._start_tick)


class TestExperiment(unittest.TestCase):

    def test_config(self):

        TESTSDIR = os.path.dirname(os.path.abspath(__file__))
        dummy_csv = os.path.join(TESTSDIR, 'dummy_trials.csv')
        dummy_json = os.path.join(TESTSDIR, 'dummy_config.json')

        # Config from dict
        test_config_dict = {'param1': 123.5, 'param2': False}
        e = Experiment(name='unittest', config=test_config_dict)
        self.assertEqual(e.config.param1, 123.5)
        self.assertFalse(e.config.param2)

        # Config from file
        e2 = Experiment(name='unittest', config=dummy_json)
        self.assertEqual(e2.config.param1, 123.5)
        self.assertFalse(e2.config.param2)

        # Config from nonexistant file
        with self.assertRaises(IOError):
            e = Experiment(name='unittest', config='NOT_A_REAL_CONFIG_FILE.dummy')

        # Config from existing but non-JSON file
        with self.assertRaises(ValueError):
            e = Experiment(name='unittest', config=dummy_csv)


    def test_add_trials(self):

        e = Experiment(name='unittest')
        self.assertEqual(len(e), 0)

        # Trial with empty params
        e.addTrials(1)
        self.assertEqual(len(e), 1)
        self.assertEqual(len(e.trials), 1)
        self.assertIsInstance(e.trials[0], Trial)

        # Initial params dict
        test_params = {'param1': 1234, 'param2': False}
        e.addTrials(2, params=test_params)
        self.assertEqual(len(e), 3)
        self.assertEqual(len(e.trials), 3)
        self.assertEqual(e.trials[1].params.param1, 1234)
        self.assertEqual(e.trials[1].params['param2'], False)

        # List params - correct length
        e.addTrials(3, list_params={'param3': [1, 2, 3]})
        self.assertEqual(len(e), 6)
        self.assertEqual(len(e.trials), 6)
        self.assertEqual(e.trials[3].params.param3, 1)
        self.assertEqual(e.trials[4].params.param3, 2)
        self.assertEqual(e.trials[5].params.param3, 3)
        
        # List params - wrong length causes exception
        with self.assertRaises(ValueError):
            e.addTrials(3, list_params={'param3': [1, 2, 3, 4]})

        # Blocks
        e2 = Experiment(name='unittest')
        e2.addTrials(1, block=2)
        e2.addTrials(1, block=1)
        self.assertEqual(e2._blocks, [1, 2])
        self.assertEqual(e2.trials[0].block, 2)


    def test_add_trials_from_csv(self):

        TESTSDIR = os.path.dirname(os.path.abspath(__file__))
        dummy_csv = os.path.join(TESTSDIR, 'dummy_trials.csv')

        # Test data, equal to dummy_trials.csv
        csv_params = [{'param5': 42, 'param4': 'True',  'param3': 2.3,      'param2': 'cat',    'param1': 1},
                      {'param5': 42, 'param4': 'False', 'param3': 1.005,    'param2': '',       'param1': 2},
                      {'param5': '', 'param4': 'False', 'param3': -4,       'param2': 'mouse',  'param1': 3},
                      {'param5': 42, 'param4': 'True',  'param3': 200000.0, 'param2': 'penguin','param1': 4}]

        # All trials in one block
        e = Experiment(name='unittest')
        e.addTrialsFromCSV(file_name=dummy_csv, sep='\t')

        self.assertEqual(len(e.trials), 4)
        self.assertEqual(e.blocks, [0])
        for ix, t in enumerate(e.trials):
            self.assertDictEqual(dict(t.params), csv_params[ix])
            self.assertEqual(t.block, e.blocks[0])

        # With block column
        e2 = Experiment(name='unittest')
        e2.addTrialsFromCSV(file_name=dummy_csv, sep='\t', block_col='param1')
        self.assertEqual(len(e2.trials), 4)
        self.assertEqual(e2.blocks, [1, 2, 3, 4])
        self.assertEqual(e2.trials[0].block, 1)
        self.assertEqual(e2.trials[1].block, 2)
        self.assertEqual(e2.trials[2].block, 3)
        self.assertEqual(e2.trials[3].block, 4)
        
        # With invalid block column name
        with self.assertRaises(ValueError):
            e2.addTrialsFromCSV(file_name=dummy_csv, sep='\t', block_col='**invalid**')
        
        # With block argument overriding column name
        e3 = Experiment(name='unittest')
        e3.addTrialsFromCSV(file_name=dummy_csv, sep='\t', block_col='param1', block=42)
        self.assertEqual(len(e2.trials), 4)
        self.assertEqual(e3.blocks, [42])
        for t in e3.trials:
            self.assertEqual(t.block, 42)

        # With params dict
        e4 = Experiment(name='unittest')
        test_params = {'param1': 1234, 'param2': False}
        e4.addTrials(2, params=test_params)
        self.assertEqual(len(e4), 2)
        self.assertEqual(e4.trials[0].params.param1, 1234)
        self.assertEqual(e4.trials[0].params['param2'], False)


    def test_add_trials_full_factorial(self):

        test_levels = {'a': 5, 'b': 3, 'c': 2}
        test_labels = {'d': ['test1', 'test2'], 'e': [1, 5, 7, 9]}

        # Factor levels
        e = Experiment(name='unittest')
        e.addTrialsFullFactorial(levels=test_levels)
        self.assertEqual(len(e), 30)

        # Factor levels with repetition
        e = Experiment(name='unittest')
        e.addTrialsFullFactorial(levels=test_levels, repeat=2)
        self.assertEqual(len(e), 60)

        # Factor levels not int
        e = Experiment(name='unittest')
        with self.assertRaises(TypeError):
            e.addTrialsFullFactorial(levels=test_levels, repeat=2.5)

        # Factor labels
        e = Experiment(name='unittest')
        e.addTrialsFullFactorial(levels=test_labels)
        self.assertEqual(len(e), 8)


    def test_save_trial_data_to_csv(self):

        # Test data 
        params = [{'param5': 42, 'param4': 'True',  'param3': 2.3,      'param2': 'cat',    'param1': 1},
                  {'param5': 42, 'param4': 'False', 'param3': 1.005,    'param2': '',       'param1': 2},
                  {'param5': '', 'param4': 'False', 'param3': -4,       'param2': 'mouse',  'param1': 3},
                  {'param5': 42, 'param4': 'True',  'param3': 200000.0, 'param2': 'penguin','param1': 4}]

        e = Experiment(name='unittest')
        e.addTrials(1, params=params[0])
        e.addTrials(1, params=params[1])
        e.addTrials(1, params=params[2])
        e.addTrials(1, params=params[3])

        fd, tmp_csv = mkstemp()
        e.saveTrialDataToCSV(file_name=tmp_csv, sep='\t')

        # Re-read temp file and compare
        e2 = Experiment(name='unittest')
        e2.addTrialsFromCSV(file_name=tmp_csv, sep='\t')
        for tidx, t in enumerate(e.trials):
            params_written = dict(t.params)
            for key in params_written:
                self.assertEqual(e.trials[tidx].params[key], e2.trials[tidx].params[key])

        os.close(fd)


    def test_trial_start_end(self):

        e = Experiment(name='unittest')
        e.addTrials(10)

        # End trial before start
        self.assertRaises(RuntimeError, e.endCurrentTrial)

        # Start and end normally
        e.startNextTrial(print_summary=False)
        self.assertEqual(e._trial_running, True)
        self.assertIsInstance(e.currentTrial, Trial)
        self.assertEqual(e.currentTrial, e.trials[0])
        self.assertTrue(e.currentTrial.running)
        self.assertFalse(e.currentTrial.done)

        last_trial = e.currentTrial
        e.endCurrentTrial(print_summary=False)
        self.assertEqual(e._trial_running, False)
        self.assertFalse(last_trial.running)
        self.assertTrue(last_trial.done)

        # Try to start a nonexisting trial
        self.assertRaises(IndexError, e.startTrial, trial_idx=20)

        # Restart a specific trial
        self.assertRaises(RuntimeError, e.startTrial, trial_idx=0)
        try:
            e.startTrial(trial_idx=0, repeat=True, print_summary=False)
        except RuntimeError:
            self.fail('Repeating trial caused exception.')

        # Start a trial object directly
        e2 = Experiment(name='unittest')
        e2.addTrials(2)
        e2.startTrial(e2.trials[0], print_summary=False)
        e2.endCurrentTrial(print_summary=False)



    def test_experiment_while_loop(self):

        e = Experiment(name='unittest')
        e.addTrials(10)

        while not e.done:
            e.startNextTrial(print_summary=False)
            e.currentTrial.results.aaa = 1
            e.endCurrentTrial(print_summary=False)
        
        # Automatically mark experiment done after last trial
        self.assertTrue(e.done)
        
        for t in e.trials:
            self.assertEqual(t.results.aaa, 1)
            self.assertTrue(t.done)


    def test_experiment_iter_loop(self):

        e = Experiment(name='unittest')
        e.addTrials(10)

        for trial in e:
            e.startTrial(trial, print_summary=False)
            trial.results.aaa = 1
            e.endCurrentTrial(print_summary=False)

        self.assertTrue(e.done)
        
        for t in e.trials:
            self.assertEqual(t.results.aaa, 1)
            self.assertTrue(t.done)


    def test_experiment_index_loop(self):

        e = Experiment(name='unittest')
        e.addTrials(10)

        for trial_no in range(0, 10):
            e.startTrial(trial_no, print_summary=False)
            e.trials[trial_no].results['aaa'] = 1
            e.endCurrentTrial(print_summary=False)

        self.assertTrue(e.done)
        
        for t in e.trials:
            self.assertEqual(t.results.aaa, 1)
            self.assertTrue(t.done)



if __name__ == '__main__':
    unittest.main()
