import unittest
from VideoAnalyzer import *
from Analyzers import *
from Models import *
from Utility import *
from DataSourceManagers import *
from DatabaseManager import *

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
        self.assertEqual(self.test_video_manager.generate_frame_filename('Suntec.mp4', 0, "01:01:01.100"), "./testData/Suntec_01:01:01.100_0.jpg")
        self.assertEqual(self.test_video_manager.generate_frame_filename(' .mp4', 0, "01:01:01.100"), "./testData/ _01:01:01.100_0.jpg")


##############################################
# Models Tests
##############################################


class VideoDataTestCase(unittest.TestCase):
    def setUp(self):
        self.test_video_data = set_up_test_video_data()

    # def test_get_captions_as_text(self):
    #     self.assertEqual(self.test_video_data.get_captions_as_text(), "a city at night. a view of a city at night. ")


##############################################
# DatabaseManager Tests
##############################################

class DBManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.test_db_manager = DBManager('https://video-analyzer-db.documents.azure.com:443/',
                                         'VREFPwEbkjNwRji7XaIjbauu2ElUc9TBgEWQsJ4OnuYJYPuHUlfD1Ru2zprjQRvKHWCouxDIbbMAt06tXKk8kA==')

    def test_create_db(self):
        dbs = self.test_db_manager.find_databases("TestDB")
        if len(dbs) == 0:
            db = self.test_db_manager.create_database("TestDB")
            self.assertEqual(db['id'], "TestDB")
        self.test_db_manager.delete_database("TestDB")

    def test_create_collections(self):
        db, collection = self.create_test_collection()

        self.assertEqual(collection["id"], "TestCll")
        self.test_db_manager.delete_database("TestDB")

    def create_test_collection(self):
        dbs = self.test_db_manager.find_databases("TestDB")
        if len(dbs) == 0:
            db = self.test_db_manager.create_database("TestDB")
        else:
            db = dbs[0]

        collections = self.test_db_manager.find_collections("TestDB", "TestCll")

        if len(collections) == 0:
            collection = self.test_db_manager.create_collection("TestDB", "TestCll", True, "V2", 400)
        else:
            collection = collections[0]

        return db, collection

    def test_create_document(self):
        test_db, test_collection = self.create_test_collection()
        document = {"id": "1", "content": "1"}
        doc = self.test_db_manager.create_doc(test_db['id'], test_collection['id'], document)
        self.assertEqual(doc['id'], document["id"])

        self.test_db_manager.delete_database("TestDB")

    def test_find_document(self):
        test_db, test_collection = self.create_test_collection()
        document = {"id": "1", "content": "1"}
        doc = self.test_db_manager.create_doc(test_db['id'], test_collection['id'], document)
        find_result = self.test_db_manager.find_doc(test_db['id'], test_collection['id'], doc['id'])
        assert len(find_result) != 0
        self.assertEqual(find_result[0]['id'], document["id"])

        self.test_db_manager.delete_database("TestDB")

    def test_query_document(self):
        test_db, test_collection = self.create_test_collection()
        document = {"id": "1", "content": "1"}
        doc = self.test_db_manager.create_doc(test_db['id'], test_collection['id'], document)
        query = {'query': 'SELECT * FROM server s'}
        query_result = self.test_db_manager.query_doc(test_db['id'], test_collection['id'], query)
        self.assertEqual(len(query_result), 1)
        self.assertEqual(doc['id'], query_result[0]["id"])

        self.test_db_manager.delete_database("TestDB")

    def test_replace_document(self):
        test_db, test_collection = self.create_test_collection()
        document = {"id": "1", "content": "1"}
        doc = self.test_db_manager.create_doc(test_db['id'], test_collection['id'], document)
        doc['name'] = "newdoc"
        self.test_db_manager.replace_doc(doc)
        query = {'query': 'SELECT * FROM server s'}
        query_result = self.test_db_manager.query_doc(test_db['id'], test_collection['id'], query)
        self.assertEqual(query_result[0]['name'], 'newdoc')

        self.test_db_manager.delete_database("TestDB")


if __name__ == '__main__':

    unittest.main()