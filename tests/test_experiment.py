import unittest

import time

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



if __name__ == '__main__':
    unittest.main()
