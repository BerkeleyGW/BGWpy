
import unittest
from collections import OrderedDict

class TestBasicInputFile(unittest.TestCase):

    def setUp(self):
        self.variables = OrderedDict([('foo', 1.1), ('bar', 2.2)])
        self.keywords = ['fizz', 'buzz']
        self.expected = 'foo 1.1\nbar 2.2\nfizz\nbuzz\n'

    def test_BasicInputFile_str(self):
        """Test the string representation of BasicInputFile."""
        from .. import BasicInputFile
        bif = BasicInputFile(self.variables, self.keywords)
        S = str(bif)
        self.assertMultiLineEqual(S, self.expected)

