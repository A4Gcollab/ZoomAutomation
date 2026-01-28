import unittest
from datetime import datetime
from src.utils import generate_names, sanitize_filename

class TestUtils(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Valid Name"), "Valid Name")
        self.assertEqual(sanitize_filename("Invalid/Name:Here"), "Invalid Name Here")
        self.assertEqual(sanitize_filename("   Multiple    Spaces   "), "Multiple Spaces")

    def test_generate_names(self):
        topic = "Weekly Sync"
        start_time = "2026-01-15T10:00:00Z"
        
        names = generate_names(topic, start_time)
        
        self.assertEqual(names['video_filename'], "20260115 Weekly Sync.mp4")
        self.assertEqual(names['transcript_filename'], "20260115 Weekly Sync_transcript.txt")
        self.assertEqual(names['youtube_title'], "20260115 Weekly Sync")
        self.assertEqual(names['date_obj'].year, 2026)
        
    def test_generate_names_complex(self):
        topic = "Project: Alpha / Review"
        start_time = "2026-12-31T23:59:59Z"
        
        names = generate_names(topic, start_time)
        self.assertEqual(names['video_filename'], "20261231 Project Alpha Review.mp4")

if __name__ == '__main__':
    unittest.main()
