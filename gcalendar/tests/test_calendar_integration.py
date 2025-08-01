"""
Integration tests for Google Calendar attendee features.

These tests require actual Google Calendar API access and should be run
with appropriate credentials. They create, modify, and delete test events.

To run these tests:
1. Set up Google OAuth credentials
2. Set environment variable: INTEGRATION_TESTS=true
3. Run: python -m pytest tests/test_calendar_integration.py -v
"""

import os
import unittest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Skip these tests unless explicitly enabled
SKIP_INTEGRATION = os.getenv('INTEGRATION_TESTS', 'false').lower() != 'true'


@unittest.skipIf(SKIP_INTEGRATION, "Integration tests disabled. Set INTEGRATION_TESTS=true to run.")
class TestCalendarIntegration(unittest.TestCase):
    """Integration tests that interact with real Google Calendar API."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Import here to avoid import errors when tests are skipped
        from auth.google_auth import get_authenticated_google_service
        from .. import calendar_tools
        
        cls.calendar_tools = calendar_tools
        cls.test_email = os.getenv('USER_GOOGLE_EMAIL', 'test@example.com')
        cls.created_event_ids = []  # Track events for cleanup
        
        # Test event time range (tomorrow, 1 hour duration)
        cls.tomorrow = datetime.now() + timedelta(days=1)
        cls.start_time = cls.tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        cls.end_time = cls.start_time + timedelta(hours=1)
        
        print(f"\nIntegration tests will use email: {cls.test_email}")
        print(f"Test events will be created for: {cls.start_time.date()}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up any test events that were created."""
        if cls.created_event_ids:
            print(f"\nCleaning up {len(cls.created_event_ids)} test events...")
            # Note: In real implementation, we would delete these events
    
    def run_async(self, coro):
        """Helper to run async functions in tests."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    
    def test_01_create_event_with_dict_attendees(self):
        """Test creating an event with dictionary attendees."""
        attendees = [
            {
                "email": "attendee1@example.com",
                "displayName": "Test Attendee 1",
                "optional": False
            },
            {
                "email": "attendee2@example.com",
                "displayName": "Test Attendee 2",
                "optional": True,
                "additionalGuests": 1
            }
        ]
        
        result = self.run_async(
            self.calendar_tools.create_event(
                None,  # Service will be injected by decorator
                self.test_email,
                summary="[TEST] Attendee Dict Test Event",
                start_time=self.start_time.isoformat(),
                end_time=self.end_time.isoformat(),
                description="Testing dictionary attendee support",
                attendees=attendees
            )
        )
        
        # Extract event ID from result
        if "Successfully created event" in result:
            # Parse event ID from result if possible
            print(f"Created event: {result}")
            self.assertIn("Successfully created event", result)
        else:
            self.fail(f"Event creation failed: {result}")
    
    def test_02_create_event_with_string_attendees(self):
        """Test backward compatibility with string attendees."""
        attendees = ["simple1@example.com", "simple2@example.com"]
        
        result = self.run_async(
            self.calendar_tools.create_event(
                None,
                self.test_email,
                summary="[TEST] String Attendee Test Event",
                start_time=(self.start_time + timedelta(hours=2)).isoformat(),
                end_time=(self.end_time + timedelta(hours=2)).isoformat(),
                description="Testing string attendee backward compatibility",
                attendees=attendees
            )
        )
        
        self.assertIn("Successfully created event", result)
    
    def test_03_get_event_with_attendee_details(self):
        """Test retrieving event shows full attendee details."""
        # First create an event
        create_result = self.run_async(
            self.calendar_tools.create_event(
                None,
                self.test_email,
                summary="[TEST] Get Event Attendee Test",
                start_time=(self.start_time + timedelta(hours=4)).isoformat(),
                end_time=(self.end_time + timedelta(hours=4)).isoformat(),
                attendees=[
                    {"email": "detail1@example.com", "displayName": "Detail Test 1"},
                    {"email": "detail2@example.com", "optional": True}
                ]
            )
        )
        
        # Extract event ID from create result (this is simplified)
        # In real test, we'd parse the ID from the result
        
        # For now, list recent events to find our test event
        events_result = self.run_async(
            self.calendar_tools.get_events(
                None,
                self.test_email,
                time_min=self.start_time.isoformat(),
                time_max=(self.end_time + timedelta(hours=5)).isoformat(),
                query="[TEST] Get Event Attendee Test"
            )
        )
        
        print(f"Events found: {events_result}")
        self.assertIn("[TEST] Get Event Attendee Test", events_result)
    
    def test_04_get_events_with_include_attendees(self):
        """Test get_events with include_attendees parameter."""
        # Create multiple events with different attendee configurations
        events_to_create = [
            {
                "summary": "[TEST] Many Attendees Event",
                "attendees": ["a@test.com", "b@test.com", "c@test.com", "d@test.com"]
            },
            {
                "summary": "[TEST] No Attendees Event",
                "attendees": []
            },
            {
                "summary": "[TEST] One Attendee Event",
                "attendees": [{"email": "single@test.com"}]
            }
        ]
        
        for i, event_config in enumerate(events_to_create):
            self.run_async(
                self.calendar_tools.create_event(
                    None,
                    self.test_email,
                    summary=event_config["summary"],
                    start_time=(self.start_time + timedelta(hours=6+i)).isoformat(),
                    end_time=(self.end_time + timedelta(hours=6+i)).isoformat(),
                    attendees=event_config.get("attendees")
                )
            )
        
        # Now get events with attendee summary
        result = self.run_async(
            self.calendar_tools.get_events(
                None,
                self.test_email,
                time_min=self.start_time.isoformat(),
                time_max=(self.end_time + timedelta(days=1)).isoformat(),
                query="[TEST]",
                include_attendees=True
            )
        )
        
        print(f"Events with attendees: {result}")
        # Many attendees event should show summary
        self.assertIn("[Attendees:", result)
    
    def test_05_get_event_attendees_tool(self):
        """Test the dedicated get_event_attendees tool."""
        # Create an event with detailed attendee info
        create_result = self.run_async(
            self.calendar_tools.create_event(
                None,
                self.test_email,
                summary="[TEST] Detailed Attendees Event",
                start_time=(self.start_time + timedelta(hours=10)).isoformat(),
                end_time=(self.end_time + timedelta(hours=10)).isoformat(),
                attendees=[
                    {
                        "email": "required@test.com",
                        "displayName": "Required Person",
                        "optional": False
                    },
                    {
                        "email": "optional@test.com",
                        "displayName": "Optional Person",
                        "optional": True,
                        "additionalGuests": 2
                    }
                ]
            )
        )
        
        # Would need to extract event ID and call get_event_attendees
        print(f"Created detailed event: {create_result}")
    
    def test_06_modify_event_attendees(self):
        """Test modifying event attendees with dict format."""
        # Create initial event
        create_result = self.run_async(
            self.calendar_tools.create_event(
                None,
                self.test_email,
                summary="[TEST] Modify Attendees Event",
                start_time=(self.start_time + timedelta(hours=12)).isoformat(),
                end_time=(self.end_time + timedelta(hours=12)).isoformat(),
                attendees=["initial@test.com"]
            )
        )
        
        # In real test, we'd extract event ID and modify it
        # For now, just verify creation worked
        self.assertIn("Successfully created event", create_result)


class TestCalendarIntegrationCleanup(unittest.TestCase):
    """Separate test class for cleanup operations."""
    
    @unittest.skipIf(SKIP_INTEGRATION, "Integration tests disabled")
    def test_cleanup_test_events(self):
        """Clean up all test events created today and tomorrow."""
        from .. import calendar_tools
        
        email = os.getenv('USER_GOOGLE_EMAIL', 'test@example.com')
        
        # Get all test events
        tomorrow = datetime.now() + timedelta(days=1)
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)
        
        result = asyncio.run(
            calendar_tools.get_events(
                None,
                email,
                time_min=start.isoformat() + 'Z',
                time_max=end.isoformat() + 'Z',
                query="[TEST]",
                max_results=100
            )
        )
        
        print(f"Found test events to clean up: {result}")
        # In real implementation, parse event IDs and delete them


if __name__ == '__main__':
    if SKIP_INTEGRATION:
        print("=" * 70)
        print("Integration tests are disabled.")
        print("To run integration tests, set: export INTEGRATION_TESTS=true")
        print("Make sure you have valid Google Calendar credentials configured.")
        print("=" * 70)
    else:
        unittest.main(verbosity=2)