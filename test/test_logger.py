# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 14:20:04 2022

@author: nyenah
"""
import unittest
import logging
import watergap_logger as log


class Testlogger(unittest.TestCase):
    """Test Logger."""

    def setUp(self):
        """
        Creatie fixtures.

        Returns
        -------
        None.

        """
        self.msg = 'testing logger'
        self.name = "log_test"

    def tearDown(self):
        """clean up test files."""
        self.remove_file = None

    def test_wronglevel(self):
        """check if error is raised when wrong logging level is entered."""
        self.level = "100"
        with self.assertRaises(ValueError):
            log.config_logger('20', self.name, self.msg)

    def test_infolevel(self):
        """Check if logger INFO level is set correctly."""
        logger = log.config_logger(logging.INFO, self.name, self.msg)
        self.assertEqual(logger.level, logging.INFO)

    def test_debuglevel(self):
        """Check if logger DEBUG level is set correctly."""
        logger = log.config_logger(logging.DEBUG, self.name, self.msg)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_criticallevel(self):
        """Check if logger CRITICAL level is set correctly."""
        logger = log.config_logger(logging.CRITICAL, self.name, self.msg)
        self.assertEqual(logger.level, logging.CRITICAL)

    def test_errorlevel(self):
        """Check if logger ERROR level is set correctly."""
        logger = log.config_logger(logging.ERROR, self.name, self.msg)
        self.assertEqual(logger.level, logging.ERROR)

    def test_warninglevel(self):
        """Check if logger WARNING level is set correctly."""
        logger = log.config_logger(logging.WARNING, self.name, self.msg)
        self.assertEqual(logger.level, logging.WARNING)
