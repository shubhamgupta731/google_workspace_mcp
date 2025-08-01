"""
Comprehensive tests for Google Calendar attendee response status features.

This test suite covers:
- Enhanced attendee display in get_event
- Include attendees parameter in get_events
- Dictionary attendee support in create_event and modify_event
- New get_event_attendees tool
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
from typing import Dict, Any, List

# Import the calendar tools
from ..calendar_tools import (
    get_event,
    get_events,
    create_event,
    modify_event,
    get_event_attendees
)


class TestCalendarAttendees(unittest.TestCase):
    """Test suite for calendar attendee functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.user_email = "test@example.com"
        self.calendar_id = "primary"
        self.event_id = "test_event_123"
        
        # Sample event data with various attendee configurations
        self.sample_event_with_attendees = {
            "id": self.event_id,
            "summary": "Test Event with Attendees",
            "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
            "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
            "htmlLink": "https://calendar.google.com/event?eid=xxx",
            "description": "Test description",
            "location": "Test location",
            "attendees": [
                {
                    "email": "organizer@example.com",
                    "displayName": "Event Organizer",
                    "responseStatus": "accepted",
                    "organizer": True,
                    "self": True
                },
                {
                    "email": "john.doe@example.com",
                    "displayName": "John Doe",
                    "responseStatus": "accepted",
                    "optional": False
                },
                {
                    "email": "jane.smith@example.com",
                    "displayName": "Jane Smith",
                    "responseStatus": "declined",
                    "optional": True,
                    "comment": "Unable to attend"
                },
                {
                    "email": "bob@example.com",
                    "responseStatus": "tentative",
                    "additionalGuests": 2
                },
                {
                    "email": "alice@example.com",
                    "responseStatus": "needsAction"
                },
                {
                    "email": "conference.room@example.com",
                    "displayName": "Conference Room A",
                    "responseStatus": "accepted",
                    "resource": True
                }
            ]
        }
        
        self.sample_event_no_attendees = {
            "id": "event_no_attendees",
            "summary": "Solo Event",
            "start": {"dateTime": "2024-01-15T14:00:00-08:00"},
            "end": {"dateTime": "2024-01-15T15:00:00-08:00"},
            "htmlLink": "https://calendar.google.com/event?eid=yyy",
            "description": "No attendees",
            "location": "Home"
        }
    
    def run_async(self, coro):
        """Helper to run async functions in tests."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


class TestGetEventAttendeeDisplay(TestCalendarAttendees):
    """Tests for enhanced attendee display in get_event."""
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_event_with_full_attendee_details(self, mock_to_thread, mock_get_service):
        """Test that get_event displays full attendee details with response status."""
        # Setup mocks
        mock_get_service.return_value = (self.mock_service, self.user_email)
        mock_to_thread.return_value = self.sample_event_with_attendees
        
        # Run test - no service argument needed
        result = self.run_async(
            get_event(user_google_email=self.user_email, event_id=self.event_id)
        )
        
        # Verify output contains attendee details with response status
        self.assertIn("Event Organizer <organizer@example.com> - accepted (organizer)", result)
        self.assertIn("John Doe <john.doe@example.com> - accepted", result)
        self.assertIn("Jane Smith <jane.smith@example.com> - declined (optional)", result)
        self.assertIn("bob@example.com - tentative", result)
        self.assertIn("alice@example.com - needsAction", result)
        self.assertIn("Conference Room A <conference.room@example.com> - accepted", result)
        
        # Verify structure
        self.assertIn("- Attendees:", result)
        self.assertIn("Event Details:", result)
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_event_no_attendees(self, mock_to_thread, mock_get_service):
        """Test get_event with no attendees."""
        mock_get_service.return_value = (self.mock_service, self.user_email)
        mock_to_thread.return_value = self.sample_event_no_attendees
        
        result = self.run_async(
            get_event(user_google_email=self.user_email, event_id="event_no_attendees")
        )
        
        self.assertIn("- Attendees:\n  - None", result)
    
    @patch('auth.google_auth.get_authenticated_google_service')
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_event_attendee_without_display_name(self, mock_to_thread, mock_get_service):
        """Test attendee display when displayName is missing."""
        mock_get_service.return_value = (self.mock_service, self.user_email)
        event = {
            **self.sample_event_no_attendees,
            "attendees": [{"email": "nodisplay@example.com", "responseStatus": "accepted"}]
        }
        mock_to_thread.return_value = event
        
        result = self.run_async(
            get_event(user_google_email=self.user_email, event_id=self.event_id)
        )
        
        self.assertIn("nodisplay@example.com - accepted", result)
        self.assertNotIn("<", result)  # No angle brackets without display name


class TestGetEventsIncludeAttendees(TestCalendarAttendees):
    """Tests for include_attendees parameter in get_events."""
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_events_default_no_attendees(self, mock_to_thread):
        """Test that get_events by default doesn't show attendee info."""
        events_result = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Meeting 1",
                    "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
                    "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
                    "htmlLink": "https://link1",
                    "attendees": [
                        {"email": "a@test.com", "responseStatus": "accepted"},
                        {"email": "b@test.com", "responseStatus": "declined"}
                    ]
                }
            ]
        }
        mock_to_thread.return_value = events_result
        
        result = self.run_async(
            get_events(self.mock_service, self.user_email)
        )
        
        # Should not contain attendee summary
        self.assertNotIn("[Attendees:", result)
        self.assertIn("Meeting 1", result)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_events_with_attendee_summary(self, mock_to_thread):
        """Test get_events with include_attendees=True shows response summary."""
        events_result = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Team Meeting",
                    "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
                    "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
                    "htmlLink": "https://link1",
                    "attendees": [
                        {"email": "a@test.com", "responseStatus": "accepted"},
                        {"email": "b@test.com", "responseStatus": "accepted"},
                        {"email": "c@test.com", "responseStatus": "declined"},
                        {"email": "d@test.com", "responseStatus": "tentative"},
                        {"email": "e@test.com", "responseStatus": "needsAction"}
                    ]
                },
                {
                    "id": "event2",
                    "summary": "Solo Work",
                    "start": {"dateTime": "2024-01-15T14:00:00-08:00"},
                    "end": {"dateTime": "2024-01-15T15:00:00-08:00"},
                    "htmlLink": "https://link2"
                    # No attendees
                }
            ]
        }
        mock_to_thread.return_value = events_result
        
        result = self.run_async(
            get_events(self.mock_service, self.user_email, include_attendees=True)
        )
        
        # Check first event has attendee summary
        self.assertIn("Team Meeting", result)
        self.assertIn("[Attendees: 2 accepted, 1 declined, 1 tentative, 1 pending]", result)
        
        # Check second event has no attendee summary
        self.assertIn("Solo Work", result)
        self.assertNotIn("Solo Work.*\\[Attendees:", result)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_events_empty_attendee_list(self, mock_to_thread):
        """Test get_events with empty attendee list."""
        events_result = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Empty Attendees",
                    "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
                    "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
                    "htmlLink": "https://link1",
                    "attendees": []
                }
            ]
        }
        mock_to_thread.return_value = events_result
        
        result = self.run_async(
            get_events(self.mock_service, self.user_email, include_attendees=True)
        )
        
        # Should not show attendee summary for empty list
        self.assertNotIn("[Attendees:", result)


class TestCreateEventWithDictAttendees(TestCalendarAttendees):
    """Tests for dictionary attendee support in create_event."""
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_create_event_string_attendees_backward_compatibility(self, mock_to_thread):
        """Test create_event with string list attendees (backward compatibility)."""
        created_event = {
            "id": "new_event",
            "summary": "New Event",
            "htmlLink": "https://calendar.google.com/event?eid=new"
        }
        mock_to_thread.return_value = created_event
        
        attendees = ["user1@example.com", "user2@example.com"]
        
        result = self.run_async(
            create_event(
                self.mock_service,
                self.user_email,
                summary="New Event",
                start_time="2024-01-20T10:00:00-08:00",
                end_time="2024-01-20T11:00:00-08:00",
                attendees=attendees
            )
        )
        
        # Verify the call was made
        mock_to_thread.assert_called()
        
        # Check that string attendees were converted to dicts
        call_args = mock_to_thread.call_args[0][0]()
        self.mock_service.events().insert.assert_called()
        insert_call_args = self.mock_service.events().insert.call_args[1]
        
        expected_attendees = [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"}
        ]
        self.assertEqual(insert_call_args['body']['attendees'], expected_attendees)
        self.assertIn("Successfully created event", result)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_create_event_dict_attendees_basic(self, mock_to_thread):
        """Test create_event with basic dictionary attendees."""
        created_event = {
            "id": "new_event",
            "summary": "Dict Event",
            "htmlLink": "https://calendar.google.com/event?eid=new"
        }
        mock_to_thread.return_value = created_event
        
        attendees = [
            {"email": "user1@example.com"},
            {"email": "user2@example.com"}
        ]
        
        result = self.run_async(
            create_event(
                self.mock_service,
                self.user_email,
                summary="Dict Event",
                start_time="2024-01-20T10:00:00-08:00",
                end_time="2024-01-20T11:00:00-08:00",
                attendees=attendees
            )
        )
        
        # Verify dict attendees passed through correctly
        call_args = mock_to_thread.call_args[0][0]()
        self.mock_service.events().insert.assert_called()
        insert_call_args = self.mock_service.events().insert.call_args[1]
        self.assertEqual(insert_call_args['body']['attendees'], attendees)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_create_event_dict_attendees_with_properties(self, mock_to_thread):
        """Test create_event with full dictionary attendees including optional fields."""
        created_event = {
            "id": "new_event",
            "summary": "Complex Event",
            "htmlLink": "https://calendar.google.com/event?eid=new"
        }
        mock_to_thread.return_value = created_event
        
        attendees = [
            {
                "email": "required@example.com",
                "displayName": "Required Attendee",
                "optional": False
            },
            {
                "email": "optional@example.com",
                "displayName": "Optional Attendee",
                "optional": True,
                "additionalGuests": 2
            }
        ]
        
        result = self.run_async(
            create_event(
                self.mock_service,
                self.user_email,
                summary="Complex Event",
                start_time="2024-01-20T10:00:00-08:00",
                end_time="2024-01-20T11:00:00-08:00",
                attendees=attendees
            )
        )
        
        # Verify complex attendees passed through
        call_args = mock_to_thread.call_args[0][0]()
        self.mock_service.events().insert.assert_called()
        insert_call_args = self.mock_service.events().insert.call_args[1]
        self.assertEqual(insert_call_args['body']['attendees'], attendees)


class TestModifyEventWithDictAttendees(TestCalendarAttendees):
    """Tests for dictionary attendee support in modify_event."""
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_modify_event_string_attendees(self, mock_to_thread):
        """Test modify_event with string attendees."""
        # Mock both get and update calls
        existing_event = {"id": self.event_id, "summary": "Existing"}
        updated_event = {
            **existing_event,
            "htmlLink": "https://calendar.google.com/event?eid=xxx"
        }
        
        mock_to_thread.side_effect = [existing_event, updated_event]
        
        attendees = ["new1@example.com", "new2@example.com"]
        
        result = self.run_async(
            modify_event(
                self.mock_service,
                self.user_email,
                self.event_id,
                attendees=attendees
            )
        )
        
        # Verify string attendees converted to dicts
        update_call = mock_to_thread.call_args_list[1][0][0]()
        self.mock_service.events().update.assert_called()
        update_call_args = self.mock_service.events().update.call_args[1]
        
        expected_attendees = [
            {"email": "new1@example.com"},
            {"email": "new2@example.com"}
        ]
        self.assertEqual(update_call_args['body']['attendees'], expected_attendees)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_modify_event_dict_attendees(self, mock_to_thread):
        """Test modify_event with dictionary attendees."""
        existing_event = {"id": self.event_id, "summary": "Existing"}
        updated_event = {
            **existing_event,
            "htmlLink": "https://calendar.google.com/event?eid=xxx"
        }
        
        mock_to_thread.side_effect = [existing_event, updated_event]
        
        attendees = [
            {
                "email": "updated@example.com",
                "displayName": "Updated User",
                "optional": True,
                "responseStatus": "tentative"  # Note: API may override this
            }
        ]
        
        result = self.run_async(
            modify_event(
                self.mock_service,
                self.user_email,
                self.event_id,
                attendees=attendees
            )
        )
        
        # Verify dict attendees passed through
        update_call = mock_to_thread.call_args_list[1][0][0]()
        self.mock_service.events().update.assert_called()
        update_call_args = self.mock_service.events().update.call_args[1]
        self.assertEqual(update_call_args['body']['attendees'], attendees)


class TestGetEventAttendees(TestCalendarAttendees):
    """Tests for the new get_event_attendees tool."""
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_event_attendees_detailed_info(self, mock_to_thread):
        """Test get_event_attendees returns comprehensive attendee details."""
        mock_to_thread.return_value = self.sample_event_with_attendees
        
        result = self.run_async(
            get_event_attendees(self.mock_service, self.user_email, self.event_id)
        )
        
        # Verify header
        self.assertIn("Attendees for event 'Test Event with Attendees'", result)
        self.assertIn("Total attendees: 6", result)
        
        # Verify individual attendee details
        self.assertIn("Attendee #1:", result)
        self.assertIn("Name: Event Organizer", result)
        self.assertIn("Email: organizer@example.com", result)
        self.assertIn("Response: accepted", result)
        self.assertIn("Status: Organizer, You", result)
        
        # Verify optional attendee
        self.assertIn("Name: Jane Smith", result)
        self.assertIn("Status: Optional", result)
        self.assertIn("Comment: Unable to attend", result)
        
        # Verify additional guests
        self.assertIn("Additional guests: 2", result)
        
        # Verify resource
        self.assertIn("Name: Conference Room A", result)
        self.assertIn("Status: Resource", result)
        
        # Verify summary
        self.assertIn("Response Summary:", result)
        self.assertIn("Accepted: 3", result)
        self.assertIn("Declined: 1", result)
        self.assertIn("Tentative: 1", result)
        self.assertIn("Pending: 1", result)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_event_attendees_no_attendees(self, mock_to_thread):
        """Test get_event_attendees with no attendees."""
        mock_to_thread.return_value = self.sample_event_no_attendees
        
        result = self.run_async(
            get_event_attendees(self.mock_service, self.user_email, "event_no_attendees")
        )
        
        self.assertEqual(
            result,
            "Event 'Solo Event' (ID: event_no_attendees) has no attendees."
        )
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_get_event_attendees_minimal_info(self, mock_to_thread):
        """Test get_event_attendees with minimal attendee information."""
        event = {
            "id": "minimal_event",
            "summary": "Minimal Event",
            "attendees": [
                {"email": "minimal@example.com"}  # Only email, all other fields missing
            ]
        }
        mock_to_thread.return_value = event
        
        result = self.run_async(
            get_event_attendees(self.mock_service, self.user_email, "minimal_event")
        )
        
        # Should handle missing fields gracefully
        self.assertIn("Email: minimal@example.com", result)
        self.assertIn("Response: needsAction", result)  # Default value
        self.assertNotIn("Name:", result)  # No display name
        self.assertNotIn("Status:", result)  # No special flags
        self.assertNotIn("Additional guests:", result)  # Zero additional guests


class TestEdgeCasesAndIntegration(TestCalendarAttendees):
    """Tests for edge cases and integration scenarios."""
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_attendee_with_all_flags(self, mock_to_thread):
        """Test attendee with all possible flags set."""
        event = {
            "id": "all_flags",
            "summary": "All Flags Event",
            "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
            "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
            "htmlLink": "https://link",
            "attendees": [
                {
                    "email": "super@example.com",
                    "displayName": "Super User",
                    "responseStatus": "accepted",
                    "organizer": True,
                    "optional": True,
                    "resource": True,
                    "self": True,
                    "comment": "Test comment",
                    "additionalGuests": 5
                }
            ]
        }
        mock_to_thread.return_value = event
        
        result = self.run_async(
            get_event(self.mock_service, self.user_email, "all_flags")
        )
        
        # Should show all flags
        self.assertIn("Super User <super@example.com> - accepted (optional) (organizer)", result)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_very_long_attendee_list(self, mock_to_thread):
        """Test event with many attendees."""
        # Create event with 50 attendees
        attendees = []
        for i in range(50):
            status = ["accepted", "declined", "tentative", "needsAction"][i % 4]
            attendees.append({
                "email": f"user{i}@example.com",
                "responseStatus": status
            })
        
        event = {
            "id": "large_event",
            "summary": "Large Event",
            "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
            "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
            "htmlLink": "https://link",
            "attendees": attendees
        }
        mock_to_thread.return_value = event
        
        result = self.run_async(
            get_event_attendees(self.mock_service, self.user_email, "large_event")
        )
        
        # Should handle large attendee list
        self.assertIn("Total attendees: 50", result)
        self.assertIn("Attendee #50:", result)
        self.assertIn("user49@example.com", result)
    
    @patch('gcalendar.calendar_tools.asyncio.to_thread')
    def test_special_characters_in_names(self, mock_to_thread):
        """Test handling of special characters in display names."""
        event = {
            "id": "special_chars",
            "summary": "Special Chars Event",
            "start": {"dateTime": "2024-01-15T10:00:00-08:00"},
            "end": {"dateTime": "2024-01-15T11:00:00-08:00"},
            "htmlLink": "https://link",
            "attendees": [
                {
                    "email": "user@example.com",
                    "displayName": "O'Brien, John (Sales) <Manager>",
                    "responseStatus": "accepted"
                }
            ]
        }
        mock_to_thread.return_value = event
        
        result = self.run_async(
            get_event(self.mock_service, self.user_email, "special_chars")
        )
        
        # Should handle special characters properly
        self.assertIn("O'Brien, John (Sales) <Manager> <user@example.com> - accepted", result)


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == '__main__':
    run_tests()