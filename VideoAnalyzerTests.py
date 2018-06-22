import unittest
from VideoAnalyzer import *
from Analyzers import *
from Models import *
from Utility import *
from DataSourceManagers import *

def set_up_test_video_data():
    test_blob_manager, test_video_manager = set_up_test_video_manager()
    test_frame_list = test_video_manager.grab_frames('SuntecTest.mp4', 0, 3, GrabRateType.BY_SECOND, 1000)
    face_analyzer, image_analyzer = set_up_test_analyzers()
    analyze_frames(test_blob_manager, test_frame_list, image_analyzer)
    analyze_faces(test_blob_manager, test_frame_list, face_analyzer)
    test_video_data = VideoData(test_frame_list)
    return test_video_data


def set_up_test_analyzers():
    image_analyzer = ImageAnalyzer("c49f0b5b59654ca28e3fec02d015c60f",
                                   "https://southeastasia.api.cognitive.microsoft.com/vision/v1.0/", "./data/")
    face_analyzer = FaceAnalyzer("7854c9ad29294ce89d2142ac0977b194",
                                 "https://southeastasia.api.cognitive.microsoft.com/face/v1.0/detect", "./data/")
    return face_analyzer, image_analyzer


def set_up_test_video_manager():
    test_blob_manager = create_blob_manager(account_name='videoanalyserstorage',
                                            account_key='0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w==')
    test_video_manager = VideoManager('./testData/', test_blob_manager)
    clear_local_files('./testData/')
    return test_blob_manager, test_video_manager


##############################################
# DataSourceManagers Tests
##############################################

class VideoManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.test_video_manager = set_up_test_video_manager()[1]

    def test_generate_frame_filename(self):
        self.assertEqual(self.test_video_manager.generate_frame_filename('Suntec.mp4', 0, "01:01:01.100"), "./testData/Suntec0_01:01:01.100.jpg")
        self.assertEqual(self.test_video_manager.generate_frame_filename(' .mp4', 0, "01:01:01.100"), "./testData/ 0_01:01:01.100.jpg")


##############################################
# Models Tests
##############################################


class VideoDataTestCase(unittest.TestCase):
    def setUp(self):
        self.test_video_data = set_up_test_video_data()

    def test_get_captions_as_text(self):
        self.assertEqual(self.test_video_data.get_captions_as_text(), "a city at night. a view of a city at night. ")

if __name__ == '__main__':

    unittest.main()