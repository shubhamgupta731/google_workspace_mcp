"""
Simple tests for calendar attendee features that work with the decorators.

These tests validate the core logic without complex mocking.
"""

import unittest
import asyncio
from unittest.mock import patch, Mock


class TestCalendarAttendeesSimple(unittest.TestCase):
    """Simple tests for attendee functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.user_email = "test@example.com"
        self.event_id = "test_event_123"
        
    def run_async(self, coro):
        """Helper to run async functions."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    async def test_get_event_formats_attendees(self, mock_to_thread, mock_get_service):
        """Test that get_event properly formats attendee information."""
        # Import here to avoid circular imports
        from ..calendar_tools import get_event
        
        # Mock the service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock the event data
        mock_event = {
            "id": self.event_id,
            "summary": "Test Event",
            "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
            "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
            "htmlLink": "https://calendar.google.com/event",
            "description": "Test",
            "location": "Online",
            "attendees": [
                {
                    "email": "organizer@example.com",
                    "displayName": "Organizer",
                    "responseStatus": "accepted",
                    "organizer": True
                },
                {
                    "email": "attendee@example.com",
                    "responseStatus": "declined",
                    "optional": True
                }
            ]
        }
        
        mock_to_thread.return_value = mock_event
        
        # Call the function - note we don't pass the service
        result = await get_event(
            user_google_email=self.user_email,
            event_id=self.event_id
        )
        
        # Verify the output contains formatted attendee info
        self.assertIn("Organizer <organizer@example.com> - accepted (organizer)", result)
        self.assertIn("attendee@example.com - declined (optional)", result)
        self.assertIn("- Attendees:", result)
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    async def test_get_events_include_attendees(self, mock_to_thread, mock_get_service):
        """Test get_events with include_attendees parameter."""
        from ..calendar_tools import get_events
        
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_events = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Meeting",
                    "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
                    "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
                    "htmlLink": "https://link",
                    "attendees": [
                        {"responseStatus": "accepted"},
                        {"responseStatus": "accepted"},
                        {"responseStatus": "declined"},
                        {"responseStatus": "needsAction"}
                    ]
                }
            ]
        }
        
        mock_to_thread.return_value = mock_events
        
        result = await get_events(
            user_google_email=self.user_email,
            include_attendees=True
        )
        
        self.assertIn("[Attendees: 2 accepted, 1 declined, 0 tentative, 1 pending]", result)
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    async def test_create_event_string_attendees(self, mock_to_thread, mock_get_service):
        """Test create_event with string attendees."""
        from ..calendar_tools import create_event
        
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Configure the mock service
        mock_events = Mock()
        mock_service.events.return_value = mock_events
        mock_insert = Mock()
        mock_events.insert.return_value = mock_insert
        
        # Mock the response
        created_event = {
            "id": "new_event",
            "summary": "Test Event",
            "htmlLink": "https://calendar.google.com/event"
        }
        mock_to_thread.return_value = created_event
        
        # Call create_event with string attendees
        result = await create_event(
            user_google_email=self.user_email,
            summary="Test Event",
            start_time="2024-01-20T10:00:00-08:00",
            end_time="2024-01-20T11:00:00-08:00",
            attendees=["user1@example.com", "user2@example.com"]
        )
        
        self.assertIn("Successfully created event", result)
        
        # Verify the mock was called
        mock_events.insert.assert_called_once()
        call_args = mock_events.insert.call_args[1]
        
        # Check that string attendees were converted to dicts
        expected_attendees = [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"}
        ]
        self.assertEqual(call_args['body']['attendees'], expected_attendees)
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    async def test_get_event_attendees_tool(self, mock_to_thread, mock_get_service):
        """Test the new get_event_attendees tool."""
        from ..calendar_tools import get_event_attendees
        
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        mock_event = {
            "id": self.event_id,
            "summary": "Test Event",
            "attendees": [
                {
                    "email": "user1@example.com",
                    "displayName": "User One",
                    "responseStatus": "accepted",
                    "optional": False
                },
                {
                    "email": "user2@example.com",
                    "displayName": "User Two",
                    "responseStatus": "declined",
                    "optional": True,
                    "comment": "Cannot attend"
                }
            ]
        }
        
        mock_to_thread.return_value = mock_event
        
        result = await get_event_attendees(
            user_google_email=self.user_email,
            event_id=self.event_id
        )
        
        # Verify detailed attendee information
        self.assertIn("Total attendees: 2", result)
        self.assertIn("Name: User One", result)
        self.assertIn("Response: accepted", result)
        self.assertIn("Name: User Two", result)
        self.assertIn("Status: Optional", result)
        self.assertIn("Comment: Cannot attend", result)
        self.assertIn("Accepted: 1", result)
        self.assertIn("Declined: 1", result)


class TestAsyncRunner(unittest.TestCase):
    """Test runner for async tests."""
    
    def test_all_async_tests(self):
        """Run all async tests."""
        test_suite = TestCalendarAttendeesSimple()
        test_suite.setUp()
        
        # List of async test methods
        async_tests = [
            test_suite.test_get_event_formats_attendees,
            test_suite.test_get_events_include_attendees,
            test_suite.test_create_event_string_attendees,
            test_suite.test_get_event_attendees_tool
        ]
        
        # Run each test
        for test in async_tests:
            try:
                asyncio.run(test())
                print(f"✓ {test.__name__}")
            except Exception as e:
                print(f"✗ {test.__name__}: {e}")
                raise


if __name__ == '__main__':
    unittest.main()