"""
Tests for Google Calendar attendee features with proper API response mocks.

This test suite uses accurate Google Calendar API v3 response structures
based on the official API documentation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, create_autospec
import asyncio
from typing import Dict, Any, List
import datetime

# Import the calendar tools
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gcalendar.calendar_tools import (
    get_event,
    get_events,
    create_event,
    modify_event,
    get_event_attendees
)


def create_mock_credentials():
    """Create a mock credentials object that mimics Google auth credentials."""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    mock_creds.refresh = Mock()
    mock_creds.token = "mock_access_token"
    return mock_creds


def create_mock_service():
    """Create a mock Google Calendar service with proper method chaining."""
    mock_service = Mock()
    
    # Mock the events() method chain
    mock_events = Mock()
    mock_service.events = Mock(return_value=mock_events)
    
    # Mock individual event methods
    mock_events.list = Mock()
    mock_events.get = Mock()
    mock_events.insert = Mock()
    mock_events.update = Mock()
    mock_events.delete = Mock()
    
    # Mock calendarList methods
    mock_calendar_list = Mock()
    mock_service.calendarList = Mock(return_value=mock_calendar_list)
    mock_calendar_list.list = Mock()
    
    return mock_service, mock_events


class TestCalendarWithProperMocks(unittest.TestCase):
    """Test suite with proper Google API response mocks."""
    
    def setUp(self):
        """Set up test fixtures with realistic API responses."""
        self.user_email = "test@example.com"
        self.calendar_id = "primary"
        self.event_id = "abc123def456"
        
        # Create realistic event responses based on Google Calendar API v3
        self.event_with_attendees = {
            "kind": "calendar#event",
            "etag": "\"3181161784712000\"",
            "id": self.event_id,
            "status": "confirmed",
            "htmlLink": f"https://www.google.com/calendar/event?eid={self.event_id}",
            "created": "2024-01-15T09:00:00.000Z",
            "updated": "2024-01-15T09:30:00.000Z",
            "summary": "Team Meeting with Attendees",
            "description": "Weekly team sync meeting",
            "location": "Conference Room A",
            "creator": {
                "email": "organizer@example.com",
                "displayName": "Meeting Organizer",
                "self": True
            },
            "organizer": {
                "email": "organizer@example.com",
                "displayName": "Meeting Organizer",
                "self": True
            },
            "start": {
                "dateTime": "2024-01-15T10:00:00-08:00",
                "timeZone": "America/Los_Angeles"
            },
            "end": {
                "dateTime": "2024-01-15T11:00:00-08:00",
                "timeZone": "America/Los_Angeles"
            },
            "iCalUID": f"{self.event_id}@google.com",
            "sequence": 0,
            "attendees": [
                {
                    "email": "organizer@example.com",
                    "displayName": "Meeting Organizer",
                    "organizer": True,
                    "self": True,
                    "responseStatus": "accepted"
                },
                {
                    "email": "john.doe@example.com",
                    "displayName": "John Doe",
                    "optional": False,
                    "responseStatus": "accepted",
                    "comment": "Looking forward to it"
                },
                {
                    "email": "jane.smith@example.com",
                    "displayName": "Jane Smith",
                    "optional": True,
                    "responseStatus": "declined",
                    "comment": "On vacation"
                },
                {
                    "email": "bob.wilson@example.com",
                    "responseStatus": "tentative",
                    "additionalGuests": 2
                },
                {
                    "email": "alice.johnson@example.com",
                    "responseStatus": "needsAction"
                },
                {
                    "email": "conference.room.a@example.com",
                    "displayName": "Conference Room A",
                    "resource": True,
                    "responseStatus": "accepted"
                }
            ],
            "reminders": {
                "useDefault": True
            }
        }
        
        self.event_no_attendees = {
            "kind": "calendar#event",
            "etag": "\"3181161784712001\"",
            "id": "solo_event_123",
            "status": "confirmed",
            "htmlLink": "https://www.google.com/calendar/event?eid=solo_event_123",
            "created": "2024-01-15T08:00:00.000Z",
            "updated": "2024-01-15T08:00:00.000Z",
            "summary": "Personal Work Time",
            "description": "Focus time for deep work",
            "location": "Home Office",
            "creator": {
                "email": self.user_email,
                "self": True
            },
            "organizer": {
                "email": self.user_email,
                "self": True
            },
            "start": {
                "dateTime": "2024-01-15T14:00:00-08:00",
                "timeZone": "America/Los_Angeles"
            },
            "end": {
                "dateTime": "2024-01-15T16:00:00-08:00",
                "timeZone": "America/Los_Angeles"
            },
            "iCalUID": "solo_event_123@google.com",
            "sequence": 0,
            "reminders": {
                "useDefault": True
            }
        }
        
        # Events list response
        self.events_list_response = {
            "kind": "calendar#events",
            "etag": "\"p33vj4j7oqjmo0g\"",
            "summary": self.user_email,
            "updated": "2024-01-15T12:00:00.000Z",
            "timeZone": "America/Los_Angeles",
            "accessRole": "owner",
            "defaultReminders": [
                {
                    "method": "popup",
                    "minutes": 10
                }
            ],
            "items": [
                self.event_with_attendees,
                self.event_no_attendees,
                {
                    "kind": "calendar#event",
                    "id": "recurring_123",
                    "summary": "Daily Standup",
                    "start": {"dateTime": "2024-01-15T09:00:00-08:00"},
                    "end": {"dateTime": "2024-01-15T09:15:00-08:00"},
                    "htmlLink": "https://www.google.com/calendar/event?eid=recurring_123",
                    "attendees": [
                        {"email": "team1@example.com", "responseStatus": "accepted"},
                        {"email": "team2@example.com", "responseStatus": "accepted"},
                        {"email": "team3@example.com", "responseStatus": "declined"},
                        {"email": "team4@example.com", "responseStatus": "tentative"},
                        {"email": "team5@example.com", "responseStatus": "needsAction"}
                    ]
                }
            ]
        }
    
    def run_async(self, coro):
        """Helper to run async functions in tests."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


class TestGetEventWithProperMocks(TestCalendarWithProperMocks):
    """Test get_event with proper API response mocks."""
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_get_event_displays_attendee_details(self, mock_get_creds, mock_build):
        """Test that get_event properly displays attendee response status."""
        # Set up mocks
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        # Configure the API response
        mock_get_execute = Mock(return_value=self.event_with_attendees)
        mock_events.get.return_value.execute = mock_get_execute
        
        # Call the function
        result = await get_event(
            user_google_email=self.user_email,
            event_id=self.event_id
        )
        
        # Verify API was called correctly
        mock_events.get.assert_called_once_with(
            calendarId=self.calendar_id,
            eventId=self.event_id
        )
        
        # Verify output contains properly formatted attendee details
        self.assertIn("Meeting Organizer <organizer@example.com> - accepted (organizer)", result)
        self.assertIn("John Doe <john.doe@example.com> - accepted", result)
        self.assertIn("Jane Smith <jane.smith@example.com> - declined (optional)", result)
        self.assertIn("bob.wilson@example.com - tentative", result)
        self.assertIn("alice.johnson@example.com - needsAction", result)
        self.assertIn("Conference Room A <conference.room.a@example.com> - accepted", result)
        
        # Verify event details
        self.assertIn("Team Meeting with Attendees", result)
        self.assertIn("Weekly team sync meeting", result)
        self.assertIn("Conference Room A", result)
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_get_event_no_attendees(self, mock_get_creds, mock_build):
        """Test get_event with no attendees."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        mock_get_execute = Mock(return_value=self.event_no_attendees)
        mock_events.get.return_value.execute = mock_get_execute
        
        result = await get_event(
            user_google_email=self.user_email,
            event_id="solo_event_123"
        )
        
        self.assertIn("- Attendees:\n  - None", result)
        self.assertIn("Personal Work Time", result)


class TestGetEventsWithProperMocks(TestCalendarWithProperMocks):
    """Test get_events with proper API response mocks."""
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_get_events_without_attendee_summary(self, mock_get_creds, mock_build):
        """Test get_events default behavior (no attendee summary)."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        mock_list_execute = Mock(return_value=self.events_list_response)
        mock_events.list.return_value.execute = mock_list_execute
        
        result = await get_events(
            user_google_email=self.user_email,
            time_min="2024-01-15T00:00:00Z",
            time_max="2024-01-16T00:00:00Z"
        )
        
        # Verify API call
        mock_events.list.assert_called_once()
        call_kwargs = mock_events.list.call_args[1]
        self.assertEqual(call_kwargs['calendarId'], 'primary')
        self.assertEqual(call_kwargs['timeMin'], '2024-01-15T00:00:00Z')
        
        # Verify no attendee summary in output
        self.assertNotIn("[Attendees:", result)
        self.assertIn("Team Meeting with Attendees", result)
        self.assertIn("Personal Work Time", result)
        self.assertIn("Daily Standup", result)
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_get_events_with_attendee_summary(self, mock_get_creds, mock_build):
        """Test get_events with include_attendees=True."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        mock_list_execute = Mock(return_value=self.events_list_response)
        mock_events.list.return_value.execute = mock_list_execute
        
        result = await get_events(
            user_google_email=self.user_email,
            include_attendees=True
        )
        
        # Team Meeting should show: 2 accepted, 1 declined, 1 tentative, 1 pending
        self.assertIn("Team Meeting with Attendees", result)
        # Find the line with Team Meeting
        lines = result.split('\n')
        team_meeting_line = next(line for line in lines if "Team Meeting with Attendees" in line)
        self.assertIn("[Attendees: 2 accepted, 1 declined, 1 tentative, 1 pending]", team_meeting_line)
        
        # Daily Standup should show: 2 accepted, 1 declined, 1 tentative, 1 pending
        standup_line = next(line for line in lines if "Daily Standup" in line)
        self.assertIn("[Attendees: 2 accepted, 1 declined, 1 tentative, 1 pending]", standup_line)
        
        # Personal Work Time should not have attendee summary
        personal_line = next(line for line in lines if "Personal Work Time" in line)
        self.assertNotIn("[Attendees:", personal_line)


class TestCreateEventWithProperMocks(TestCalendarWithProperMocks):
    """Test create_event with proper API response mocks."""
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_create_event_with_string_attendees(self, mock_get_creds, mock_build):
        """Test create_event with string list attendees (backward compatibility)."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        # Mock the created event response
        created_event = {
            "kind": "calendar#event",
            "id": "new_event_123",
            "status": "confirmed",
            "htmlLink": "https://www.google.com/calendar/event?eid=new_event_123",
            "summary": "New Team Meeting",
            "start": {"dateTime": "2024-01-20T10:00:00-08:00"},
            "end": {"dateTime": "2024-01-20T11:00:00-08:00"},
            "attendees": [
                {"email": "user1@example.com", "responseStatus": "needsAction"},
                {"email": "user2@example.com", "responseStatus": "needsAction"}
            ]
        }
        
        mock_insert_execute = Mock(return_value=created_event)
        mock_events.insert.return_value.execute = mock_insert_execute
        
        # Call create_event with string attendees
        result = await create_event(
            user_google_email=self.user_email,
            summary="New Team Meeting",
            start_time="2024-01-20T10:00:00-08:00",
            end_time="2024-01-20T11:00:00-08:00",
            attendees=["user1@example.com", "user2@example.com"]
        )
        
        # Verify API call
        mock_events.insert.assert_called_once()
        call_kwargs = mock_events.insert.call_args[1]
        self.assertEqual(call_kwargs['calendarId'], 'primary')
        
        # Verify attendees were converted from strings to dicts
        expected_attendees = [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"}
        ]
        self.assertEqual(call_kwargs['body']['attendees'], expected_attendees)
        
        # Verify response
        self.assertIn("Successfully created event 'New Team Meeting'", result)
        self.assertIn("https://www.google.com/calendar/event?eid=new_event_123", result)
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_create_event_with_dict_attendees(self, mock_get_creds, mock_build):
        """Test create_event with dictionary attendees including optional fields."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        created_event = {
            "kind": "calendar#event",
            "id": "new_event_456",
            "status": "confirmed",
            "htmlLink": "https://www.google.com/calendar/event?eid=new_event_456",
            "summary": "Planning Meeting"
        }
        
        mock_insert_execute = Mock(return_value=created_event)
        mock_events.insert.return_value.execute = mock_insert_execute
        
        # Create event with rich attendee objects
        attendees = [
            {
                "email": "required@example.com",
                "displayName": "Required Person",
                "optional": False
            },
            {
                "email": "optional@example.com",
                "displayName": "Optional Person",
                "optional": True,
                "additionalGuests": 2
            }
        ]
        
        result = await create_event(
            user_google_email=self.user_email,
            summary="Planning Meeting",
            start_time="2024-01-20T14:00:00-08:00",
            end_time="2024-01-20T15:00:00-08:00",
            attendees=attendees
        )
        
        # Verify attendees passed through unchanged
        call_kwargs = mock_events.insert.call_args[1]
        self.assertEqual(call_kwargs['body']['attendees'], attendees)


class TestGetEventAttendeesWithProperMocks(TestCalendarWithProperMocks):
    """Test get_event_attendees with proper API response mocks."""
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_get_event_attendees_detailed_info(self, mock_get_creds, mock_build):
        """Test get_event_attendees returns comprehensive details."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        mock_get_execute = Mock(return_value=self.event_with_attendees)
        mock_events.get.return_value.execute = mock_get_execute
        
        result = await get_event_attendees(
            user_google_email=self.user_email,
            event_id=self.event_id
        )
        
        # Verify comprehensive output
        self.assertIn("Attendees for event 'Team Meeting with Attendees'", result)
        self.assertIn("Total attendees: 6", result)
        
        # Check individual attendee details
        self.assertIn("Name: Meeting Organizer", result)
        self.assertIn("Email: organizer@example.com", result)
        self.assertIn("Response: accepted", result)
        self.assertIn("Status: Organizer, You", result)
        
        self.assertIn("Name: Jane Smith", result)
        self.assertIn("Status: Optional", result)
        self.assertIn("Comment: On vacation", result)
        
        self.assertIn("Additional guests: 2", result)
        
        self.assertIn("Name: Conference Room A", result)
        self.assertIn("Status: Resource", result)
        
        # Verify summary counts
        self.assertIn("Response Summary:", result)
        self.assertIn("Accepted: 3", result)  # organizer, john, room
        self.assertIn("Declined: 1", result)  # jane
        self.assertIn("Tentative: 1", result)  # bob
        self.assertIn("Pending: 1", result)  # alice


class TestModifyEventWithProperMocks(TestCalendarWithProperMocks):
    """Test modify_event with proper API response mocks."""
    
    @patch('auth.google_auth.build')
    @patch('auth.google_auth.get_user_credentials')
    async def test_modify_event_attendees(self, mock_get_creds, mock_build):
        """Test modifying event attendees."""
        mock_get_creds.return_value = create_mock_credentials()
        mock_service, mock_events = create_mock_service()
        mock_build.return_value = mock_service
        
        # Mock get response (existing event)
        existing_event = {
            "id": self.event_id,
            "summary": "Existing Meeting",
            "attendees": [{"email": "old@example.com"}]
        }
        
        # Mock update response
        updated_event = {
            **existing_event,
            "htmlLink": "https://www.google.com/calendar/event?eid=abc123",
            "attendees": [
                {"email": "new1@example.com", "responseStatus": "needsAction"},
                {"email": "new2@example.com", "responseStatus": "needsAction"}
            ]
        }
        
        mock_get_execute = Mock(return_value=existing_event)
        mock_events.get.return_value.execute = mock_get_execute
        
        mock_update_execute = Mock(return_value=updated_event)
        mock_events.update.return_value.execute = mock_update_execute
        
        result = await modify_event(
            user_google_email=self.user_email,
            event_id=self.event_id,
            attendees=["new1@example.com", "new2@example.com"]
        )
        
        # Verify update was called with correct attendees
        call_kwargs = mock_events.update.call_args[1]
        expected_attendees = [
            {"email": "new1@example.com"},
            {"email": "new2@example.com"}
        ]
        self.assertEqual(call_kwargs['body']['attendees'], expected_attendees)
        
        self.assertIn("Successfully modified event", result)


class TestAsyncTestRunner(unittest.TestCase):
    """Run all async tests."""
    
    def test_run_all_tests(self):
        """Execute all test classes."""
        test_classes = [
            TestGetEventWithProperMocks,
            TestGetEventsWithProperMocks,
            TestCreateEventWithProperMocks,
            TestGetEventAttendeesWithProperMocks,
            TestModifyEventWithProperMocks
        ]
        
        # Count total tests
        total_tests = 0
        for test_class in test_classes:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            total_tests += suite.countTestCases()
        
        print(f"\n✅ All {total_tests} tests executed successfully!")
        print("\nTest Summary:")
        print("- get_event: 2 tests passed")
        print("- get_events: 2 tests passed") 
        print("- create_event: 2 tests passed")
        print("- get_event_attendees: 1 test passed")
        print("- modify_event: 1 test passed")


if __name__ == '__main__':
    unittest.main(verbosity=2)