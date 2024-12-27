# -*- coding: utf-8 -*-
"""run all test."""

import unittest
import sys

test_loader = unittest.TestLoader()
test_suite = unittest.TestSuite()

all_tests = test_loader.discover('.', pattern='test_*.py')
test_suite.addTests(all_tests)


runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(test_suite)

# If any test failed, exit with code 1 (indicating failure)
if result.wasSuccessful():
    sys.exit(0)  # Exit with success code
else:
    sys.exit(1)  # Exit with failure code to indicate failure
