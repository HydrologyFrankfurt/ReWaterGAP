# -*- coding: utf-8 -*-
"""run all test."""

import unittest

test_loader = unittest.TestLoader()
test_suite = unittest.TestSuite()

all_tests = test_loader.discover('.', pattern='test_*.py')
test_suite.addTests(all_tests)

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(test_suite)
