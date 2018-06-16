import unittest
from VideoAnalyzer import *


class VideoAnalyzerTestCase(unittest.TestCase):
    def test_generate_frame_filename(self):
        blob = BlobManager(account_name='videoanalyserstorage',
                       account_key='0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w==')
        video_manager = VideoManager('./data/', blob)
        self.assertEqual(video_manager.generate_frame_filename('Suntec.mp4', 0, "01:01:01.100"), "./data/Suntec0_01:01:01.100.jpg")
        self.assertEqual(video_manager.generate_frame_filename(' .mp4', 0, "01:01:01.100"), "./data/ 0_01:01:01.100.jpg")


if __name__ == '__main__':
    unittest.main()