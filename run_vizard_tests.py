import unittest

import tests.test_experiment as test_experiment
import tests.test_data as test_data

print('Running unit tests from within Vizard environment...')

print('experiment')
unittest.main(module=test_experiment, exit=False)

print('data')
unittest.main(module=test_data)

print('recorder')
unittest.main(module=test_recorder)

print('replay')
unittest.main(module=test_replay)
