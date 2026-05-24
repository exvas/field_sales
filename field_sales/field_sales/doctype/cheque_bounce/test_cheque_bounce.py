"""Stub test module so bench's test discovery doesn't error on this DocType."""

import unittest


class TestChequeBounce(unittest.TestCase):
    def test_smoke(self):
        self.assertTrue(True)
