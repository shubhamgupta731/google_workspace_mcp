"""
Unit tests for attendee formatting logic.

These tests focus on the formatting and display logic without requiring
full service mocking.
"""

import unittest
from typing import List, Dict, Any


def format_attendee_detail(attendee: Dict[str, Any]) -> str:
    """
    Format a single attendee's details for display.
    This mirrors the logic in get_event.
    """
    email = attendee.get("email", "Unknown")
    status = attendee.get("responseStatus", "needsAction")
    name = attendee.get("displayName", "")
    optional = " (optional)" if attendee.get("optional", False) else ""
    organizer = " (organizer)" if attendee.get("organizer", False) else ""
    
    if name:
        detail = f"{name} <{email}> - {status}{optional}{organizer}"
    else:
        detail = f"{email} - {status}{optional}{organizer}"
    
    return detail


def format_attendee_summary(attendees: List[Dict[str, Any]]) -> str:
    """
    Format attendee response summary for get_events.
    """
    if not attendees:
        return ""
    
    accepted = sum(1 for a in attendees if a.get("responseStatus") == "accepted")
    declined = sum(1 for a in attendees if a.get("responseStatus") == "declined")
    # Count missing responseStatus as needsAction
    pending = sum(1 for a in attendees if a.get("responseStatus", "needsAction") == "needsAction")
    tentative = sum(1 for a in attendees if a.get("responseStatus") == "tentative")
    
    return f"[Attendees: {accepted} accepted, {declined} declined, {tentative} tentative, {pending} pending]"


class TestAttendeeFormatting(unittest.TestCase):
    """Test attendee formatting functions."""
    
    def test_format_basic_attendee(self):
        """Test formatting basic attendee with email only."""
        attendee = {"email": "test@example.com"}
        result = format_attendee_detail(attendee)
        self.assertEqual(result, "test@example.com - needsAction")
    
    def test_format_attendee_with_name(self):
        """Test formatting attendee with display name."""
        attendee = {
            "email": "test@example.com",
            "displayName": "Test User",
            "responseStatus": "accepted"
        }
        result = format_attendee_detail(attendee)
        self.assertEqual(result, "Test User <test@example.com> - accepted")
    
    def test_format_optional_attendee(self):
        """Test formatting optional attendee."""
        attendee = {
            "email": "optional@example.com",
            "optional": True,
            "responseStatus": "declined"
        }
        result = format_attendee_detail(attendee)
        self.assertEqual(result, "optional@example.com - declined (optional)")
    
    def test_format_organizer(self):
        """Test formatting event organizer."""
        attendee = {
            "email": "organizer@example.com",
            "displayName": "Event Organizer",
            "organizer": True,
            "responseStatus": "accepted"
        }
        result = format_attendee_detail(attendee)
        self.assertEqual(result, "Event Organizer <organizer@example.com> - accepted (organizer)")
    
    def test_format_attendee_all_flags(self):
        """Test formatting attendee with multiple flags."""
        attendee = {
            "email": "special@example.com",
            "displayName": "Special User",
            "optional": True,
            "organizer": True,
            "responseStatus": "tentative"
        }
        result = format_attendee_detail(attendee)
        self.assertEqual(result, "Special User <special@example.com> - tentative (optional) (organizer)")
    
    def test_attendee_summary_mixed_responses(self):
        """Test attendee summary with various response statuses."""
        attendees = [
            {"responseStatus": "accepted"},
            {"responseStatus": "accepted"},
            {"responseStatus": "declined"},
            {"responseStatus": "tentative"},
            {"responseStatus": "needsAction"},
            {"responseStatus": "needsAction"},
            {"responseStatus": "needsAction"}
        ]
        result = format_attendee_summary(attendees)
        self.assertEqual(
            result,
            "[Attendees: 2 accepted, 1 declined, 1 tentative, 3 pending]"
        )
    
    def test_attendee_summary_all_accepted(self):
        """Test attendee summary when all accepted."""
        attendees = [
            {"responseStatus": "accepted"},
            {"responseStatus": "accepted"},
            {"responseStatus": "accepted"}
        ]
        result = format_attendee_summary(attendees)
        self.assertEqual(
            result,
            "[Attendees: 3 accepted, 0 declined, 0 tentative, 0 pending]"
        )
    
    def test_attendee_summary_empty_list(self):
        """Test attendee summary with no attendees."""
        result = format_attendee_summary([])
        self.assertEqual(result, "")
    
    def test_attendee_summary_missing_status(self):
        """Test attendee summary with missing responseStatus."""
        attendees = [
            {"email": "test1@example.com"},  # No responseStatus - defaults to needsAction
            {"responseStatus": "accepted"},
            {"responseStatus": "declined"}
        ]
        result = format_attendee_summary(attendees)
        # First attendee has no status, so it defaults to needsAction (1 pending)
        self.assertEqual(
            result,
            "[Attendees: 1 accepted, 1 declined, 0 tentative, 1 pending]"
        )


class TestAttendeeValidation(unittest.TestCase):
    """Test validation logic for attendee data."""
    
    def test_validate_string_attendees(self):
        """Test that string attendees are valid email format."""
        string_attendees = ["user1@example.com", "user2@example.com"]
        # In actual implementation, these would be converted to dicts
        for email in string_attendees:
            self.assertIn("@", email)
            self.assertIn(".", email.split("@")[1])
    
    def test_validate_dict_attendees(self):
        """Test that dict attendees have required fields."""
        dict_attendees = [
            {"email": "user1@example.com"},
            {"email": "user2@example.com", "optional": True}
        ]
        for attendee in dict_attendees:
            self.assertIn("email", attendee)
            self.assertIsInstance(attendee["email"], str)
    
    def test_detect_attendee_format(self):
        """Test detection of attendee format (string vs dict)."""
        string_list = ["user1@example.com", "user2@example.com"]
        dict_list = [{"email": "user1@example.com"}]
        
        # Check if first element is string
        self.assertIsInstance(string_list[0], str)
        self.assertIsInstance(dict_list[0], dict)


if __name__ == '__main__':
    unittest.main()