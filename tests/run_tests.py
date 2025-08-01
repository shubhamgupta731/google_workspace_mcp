#!/usr/bin/env python
"""
Test runner for Google Workspace MCP calendar attendee features.

This script runs all tests related to the attendee response status functionality.
"""

import sys
import os
import unittest
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_all_tests():
    """Run all tests and display results."""
    print("=" * 70)
    print("Running Google Calendar Attendee Feature Tests")
    print("=" * 70)
    print()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback.splitlines()[-1]}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback.splitlines()[-1]}")
    
    return result.wasSuccessful()


def run_specific_test_class(test_class_name):
    """Run a specific test class."""
    print(f"Running tests for: {test_class_name}")
    print("=" * 70)
    
    # Import the test module
    from tests.test_calendar_attendees import (
        TestGetEventAttendeeDisplay,
        TestGetEventsIncludeAttendees,
        TestCreateEventWithDictAttendees,
        TestModifyEventWithDictAttendees,
        TestGetEventAttendees,
        TestEdgeCasesAndIntegration
    )
    
    # Map class names to actual classes
    test_classes = {
        'TestGetEventAttendeeDisplay': TestGetEventAttendeeDisplay,
        'TestGetEventsIncludeAttendees': TestGetEventsIncludeAttendees,
        'TestCreateEventWithDictAttendees': TestCreateEventWithDictAttendees,
        'TestModifyEventWithDictAttendees': TestModifyEventWithDictAttendees,
        'TestGetEventAttendees': TestGetEventAttendees,
        'TestEdgeCasesAndIntegration': TestEdgeCasesAndIntegration
    }
    
    if test_class_name in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_class_name])
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    else:
        print(f"Test class '{test_class_name}' not found!")
        print(f"Available classes: {', '.join(test_classes.keys())}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test class if provided
        success = run_specific_test_class(sys.argv[1])
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)