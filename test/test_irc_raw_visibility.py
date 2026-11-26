import unittest

from gdo.irc.method.irc_raw import irc_raw


class IrcRawVisibilityTest(unittest.TestCase):
    def test_raw_is_hidden(self):
        self.assertTrue(irc_raw.gdo_method_hidden(object.__new__(irc_raw)))
