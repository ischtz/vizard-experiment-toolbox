import unittest

import os
import json
from tempfile import mkstemp

from vzgazetoolbox.data import ParamSet


class TestParamSet(unittest.TestCase):

    def test_input_dict(self):
        
        # Input dict
        test_dict = {'a': 1, 'b': 2}
        p = ParamSet(input_dict=test_dict)
        self.assertDictContainsSubset(test_dict, p.__dict__)

        # Input other ParamSet
        p2 = ParamSet(input_dict=p)
        self.assertDictContainsSubset(test_dict, p2.__dict__)

        # All other input types
        test_inputs = ['string', 1, False, [1, 2]]
        for ti in test_inputs:
            self.assertRaises(ValueError, ParamSet, input_dict=ti)


    def test_item_retrieval(self):
        p = ParamSet()
        
        p.a = 'first_item'
        self.assertEqual(p['a'], 'first_item')
        p['b'] = 'second_item'
        self.assertEqual(p.b, 'second_item')
        self.assertDictContainsSubset({'a': 'first_item', 'b': 'second_item'}, p.__dict__)


    def test_json(self):
        test_dict = {'a': 1, 'b': '2', 'c': [0, 1, True], 'd': False}
        p = ParamSet(input_dict=test_dict)

        # String export
        json_data = p.toJSON()
        compare = json.loads(json_data)
        self.assertDictEqual(p.__dict__, compare)

        # File export
        fd, json_tmpfile = mkstemp()
        p.toJSONFile(json_file=json_tmpfile)
        with open(json_tmpfile, 'r') as jf:
            compare2 = json.load(jf)
            self.assertDictEqual(p.__dict__, compare2)
        
        # Creation from JSON file
        p_new = ParamSet.fromJSONFile(json_file=json_tmpfile)
        self.assertIsInstance(p_new, ParamSet)
        self.assertDictEqual(p_new.__dict__, compare2)
        os.close(fd)


    def test_empty_param_set(self):

        p = ParamSet()
        self.assertEqual(len(p), 0)
        self.assertEqual(repr(p), '{}')
        self.assertEqual(str(p), 'Empty parameter set.')


if __name__ == '__main__':
    unittest.main()
