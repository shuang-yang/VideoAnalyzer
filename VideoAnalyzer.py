
from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

import cv2 as cv
import numpy as np
import moviepy.editor as mp
import os
import requests
import collections
import functools
import json
import time
import nltk
import sys
import matplotlib.pyplot as plt
# import unirest
from PIL import Image
import pydocumentdb
import pydocumentdb.document_client as dc
from flask import *
from enum import Enum
from azure.storage.blob import BlockBlobService, PublicAccess
from concurrent import futures
from wordcloud import WordCloud
from Models import *
from Utility import *
from Analyzers import *
from DataSourceManagers import *
from DatabaseManager import *
from SearchManager import *
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from threading import Thread, Semaphore

CONFIDENCE_THRESHOLD = 0.5

db_config = {
    "ENDPOINT": 'https://video-analyzer-db.documents.azure.com:443/',
    "MASTERKEY": 'VREFPwEbkjNwRji7XaIjbauu2ElUc9TBgEWQsJ4OnuYJYPuHUlfD1Ru2zprjQRvKHWCouxDIbbMAt06tXKk8kA==',
}


def create_blob_manager(account_name='videoanalyserstorage', account_key='0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w=='):
    blob = BlobManager(account_name=account_name,
                       account_key=account_key)
    blob.clear()
    blob.create_container('video')
    blob.create_container('image')
    blob.create_container('audio')
    return blob


def generate_word_clouds_from_frames(video_data):
    # Obtain top n keywords
    top_keywords = video_data.top_keywords_from_frames(10)
    top_caption_keywords = video_data.top_caption_keywords_from_frames(10)
    # Generate wordcloud
    font_path = 'Symbola.ttf'
    word_cloud = WordCloud(background_color="white", font_path=font_path).generate_from_frequencies(dict(top_keywords))
    word_cloud.to_file('Suntec_tags_word_cloud.jpg')
    word_cloud = WordCloud(background_color="white", font_path=font_path).generate_from_frequencies(
        dict(top_caption_keywords))
    word_cloud.to_file('Suntec_captions_word_cloud.jpg')


def analyze_frames(blob, frame_list, image_analyzer, filename, db_manager, video_id):
    # Obtain a list of analyses based on the sampled frames asynchronously
    urls = []
    for b in blob.list_blobs('image'):
        urls.append(blob.get_blob_url('image', b.name))
    analyses = image_analyzer.analyze_remote_by_batch(urls)

    # Print json information to file
    output_file = open("./data/Output_image_json_" + filename + ".txt", "w")
    index = 0
    for analysis in analyses:
        output_file.write('Frame ' + str(index) + ' : ' + '\n\n')
        json.dump(analysis, output_file)
        output_file.write('\n\n\n')
        index += 1
    output_file.close()

    # Add Image analyses result to frames
    image_data_list = map(lambda x: image_analyzer.convert_to_image_data(x), analyses)
    frame_to_data_list = list(zip(frame_list, image_data_list))

    for frame, image_data in frame_to_data_list:
        # Set image_data of frames
        frame.set_image_data(image_data)

        # Create Unique Cosmos DB ID
        new_id = str(video_id) + '_' + str(frame.video_time)

        # Add db_entry based on image_data of the frame
        # TODO - consider using Collection instead of joining them all in a string
        tags =','.join(image_data.tags)
        captions = ','.join([caption[0] for caption in image_data.captions if caption[1] >= Constants.CONFIDENCE_THRESHOLD ])
        celebrities = ','.join([celebrity[0] for celebrity in image_data.celebrities if celebrity[1] >= Constants.CONFIDENCE_THRESHOLD])
        landmarks = ','.join([landmark[0] for landmark in image_data.landmarks if landmark[1] >= Constants.CONFIDENCE_THRESHOLD])
        categories = ','.join([category[0] for category in image_data.categories if category[1] >= Constants.CONFIDENCE_THRESHOLD])
        dominant_colors = ','.join(image_data.dominant_colors)

        doc = {'id': new_id, 'video_id': video_id, 'filename': filename,
               'index': frame.index, 'time': frame.video_time, 'url': frame.url,
               'tags': tags, 'captions': captions, 'categories': categories, 'celebrities': celebrities, 'landmarks': landmarks,
               'dominant_colors': dominant_colors, 'foreground_color': image_data.foreground_color, 'background_color': image_data.background_color,
               'accent_color': image_data.accent_color, 'isBwImg': image_data.isBwImg, 'height': image_data.height, 'width': image_data.width}

        if db_manager.find_doc(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, doc['id']):
            db_manager.replace_doc(doc)
        else:
            db_entry = db_manager.create_doc(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, doc)
            frame.set_db_entry(db_entry)

    # # print tags text to file
    # outputtags_file = open("./data/Output_tags_" + filename + ".txt", "w")
    # for frame, image_data in frame_to_data_list:
    #     outputtags_file.write('Frame at: ' + ms_to_std_time(frame.video_time) + '\n tags: \n' + str(image_data.tags) + '\n\n')
    # outputtags_file.close()


def analyze_faces(blob, frame_list, face_analyzer, filename, db_manager):
    # Obtain a list of analyses based on the grabbed frames
    urls = list(map(lambda x: blob.get_blob_url('image', x.name), blob.list_blobs('image')))
    analyses = face_analyzer.analyze_remote_by_batch(urls)
    # print json info to file
    output_json_file = open("./data/Output_faces_json_" + filename + ".txt", "w")
    for analysis in analyses:
        json.dump(analysis, output_json_file)
    output_json_file.close()

    # Add Image analyses result to frames
    face_data_lists = map(lambda x: face_analyzer.convert_to_face_data(x), analyses)
    frame_to_face_data_list = list(zip(frame_list, face_data_lists))
    output_file = open("./data/Output_frame_faces_" + filename + ".txt", "w")
    for frame, face_data_list in frame_to_face_data_list:
        frame.set_face_data_list(face_data_list)
        output_file.write('Frame at ' + ms_to_std_time(frame.video_time) + ': \n')
        output_file.write('Dominant emotion: \n')
        for emotion in frame.get_predominant_emotions(2):
            output_file.write(str(emotion) + '\n')
        output_file.write('Faces: \n')
        for face in face_data_list:
            output_file.write(" face " + str(face.id) + '\n')
        output_file.write('\n\n')
    output_file.close()


def extract_keywords_from_captions(text_analyzer, filename_no_extension, db_manager, db_entry):
    # print('Extract keywords - filepath : ' + filepath)
    filename = 'Output_captions_' + filename_no_extension + '.txt'
    analysis = text_analyzer.analyze_local(filename,
                                           TextAnalyticsService.KEY_PHRASES.value)
    # print key phrase text to file
    output_file = open("./data/Output_key_phrases_" + filename_no_extension + ".txt", "w")
    json.dump(analysis, output_file)

    # Add key phrases to db
    db_entry['caption_keywords'] = ', '.join(analysis['documents'][0]['keyPhrases'])
    db_manager.replace_doc(db_entry)
    output_file.close()


def extract_keywords_from_tags(video_data, db_manager, db_entry, num):
    top_frequent_tags = video_data.top_keywords_from_tags(num)
    keywords_string = ""
    for tag in top_frequent_tags:
        keywords_string += tag[0] + ", "
    db_entry['tags_keywords'] = keywords_string
    db_manager.replace_doc(db_entry)


def summerize_captions(filename_no_extension):
    filepath = os.path.join('./data/Output_captions_', filename_no_extension + '.txt')
    parser = PlaintextParser.from_file(filepath, Tokenizer("english"))
    stemmer = Stemmer("english")
    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words("english")
    for sentence in summarizer(parser.document, 5):
        print(sentence)


def init_analyzers():
    image_analyzer = ImageAnalyzer("c49f0b5b59654ca28e3fec02d015c60f",
                                   "https://southeastasia.api.cognitive.microsoft.com/vision/v1.0/", "./data/", 10)
    face_analyzer = FaceAnalyzer("7854c9ad29294ce89d2142ac0977b194",
                                 "https://southeastasia.api.cognitive.microsoft.com/face/v1.0/detect", "./data/", 9)
    text_analyzer = TextAnalyzer("5105a7087a364ba4a3b9467ca9f094ce",
                                 "https://southeastasia.api.cognitive.microsoft.com/text/analytics/v2.0/", './data/')
    return image_analyzer, face_analyzer, text_analyzer


def get_caption_as_text(video_data, filename, db_manager, db_entry):
    output_file = open("./data/Output_captions_" + filename + ".txt", "w")
    output_file.write(video_data.get_captions_as_text())
    db_entry['captions'] = video_data.get_captions_as_text()
    db_manager.replace_doc(db_entry)
    output_file.close()


def extract_dominant_colors(video_data, db_manager, db_entry, num):
    dominant_colors_str = ""
    dominant_colors = video_data.get_dominant_colors(num)
    for color in dominant_colors:
        dominant_colors_str += color[0] + ', '
    db_entry['dominant_colors'] = dominant_colors_str
    db_manager.replace_doc(db_entry)


def analyze_video(filename, start, end, sampling_type, sampling_rate, blob_manager, video_manager, db_manager):

    # Initiate Analyzers
    image_analyzer, face_analyzer, text_analyzer = init_analyzers()

    # Generate Filename
    filename_no_extension = os.path.splitext(filename)[0]

    # Generate new CosmosDB id
    mutex = Semaphore(1)
    mutex.acquire()
    new_video_id = db_manager.get_next_id(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT)
    mutex.release()

    # Create CosmosDB entry
    doc_summarized = {'id': str(new_video_id), 'name': filename_no_extension}
    db_entry_summarized = db_manager.create_doc(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT, doc_summarized)

    # Generate a list of frames
    frame_list = video_manager.grab_frames(filename, start, end, sampling_type, sampling_rate)

    # Analyze frames with Computer Vision API
    analyze_frames(blob_manager, frame_list, image_analyzer, filename_no_extension, db_manager, new_video_id)

    # Analyze frames with Face API
    analyze_faces(blob_manager, frame_list, face_analyzer, filename_no_extension, db_manager)

    # Generate a VideoData object from the list of frames
    video_data = VideoData(frame_list)

    # Extract most frequent keywords from captions
    get_caption_as_text(video_data, filename_no_extension, db_manager, db_entry_summarized)
    extract_keywords_from_captions(text_analyzer, filename_no_extension, db_manager, db_entry_summarized)

    # Extract most frequent keywords from tags
    extract_keywords_from_tags(video_data, db_manager, db_entry_summarized, 10)

    # Extract most dominant colors of the video
    extract_dominant_colors(video_data, db_manager, db_entry_summarized, 3)

    return db_entry_summarized, video_data


def search_locally(keyword):
    search_result = video_data.search_with_keyword(keyword)
    for result in search_result:
        print('Keyword ' + keyword + ' found at frame:' + ms_to_std_time(result.video_time))
        # image = Image.open(result.filename)
        # image.show()


def search(keyword):
    search_manager = SearchManager("video-analyzer-search", "2017-11-11",
                                   'https://video-analyzer-search.search.windows.net',
                                   '40BCFD3875D09243AB49A3175FE9AD99')
    response = search_manager.search(Constants.SEARCH_INDEX_NAME_DEFAULT, keyword)
    return response.json()


# Main Execution Body
if __name__ == '__main__':
    start = time.time()
    print('Starting: ' + str(start) + '\n')

    try:
        # Clears any legacy files
        clear_local_files('./data/')

        # Initialze Azure Blob Storage managers
        blob_manager = create_blob_manager()

        # Initialze Video Manager
        video_manager = VideoManager('./data/', blob_manager)

        # Initialze Cosmos DB Manager
        db_manager = DBManager(db_config["ENDPOINT"], db_config["MASTERKEY"])

        # Create output cosmos DB for both video and extracted info from video
        db_videos = db_manager.read_database(Constants.DB_NAME_VIDEOS) if len(db_manager.find_databases(Constants.DB_NAME_VIDEOS)) != 0 \
            else db_manager.create_database(Constants.DB_NAME_VIDEOS)
        db_frames = db_manager.read_database(Constants.DB_NAME_FRAMES) if len(db_manager.find_databases(Constants.DB_NAME_FRAMES)) != 0 \
            else db_manager.create_database(Constants.DB_NAME_FRAMES)

        collection_videos = db_manager.read_collection(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT) if len(db_manager.find_collections(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT)) != 0 \
            else db_manager.create_collection(Constants.DB_NAME_VIDEOS, Constants.COLLECTION_NAME_DEFAULT, True, "V2", 400)
        collection_frames = db_manager.read_collection(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT) if len(db_manager.find_collections(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT)) != 0 \
            else db_manager.create_collection(Constants.DB_NAME_FRAMES, Constants.COLLECTION_NAME_DEFAULT, True, "V2", 400)

        # Analyze video with specified parameters: start time, end time, sampling rate
        db_entry, video_data = analyze_video('Filipino_news3.mp4', start=0, end=80, sampling_type=GrabRateType.BY_SECOND,
                      sampling_rate=1000, blob_manager=blob_manager, video_manager=video_manager, db_manager=db_manager)

        # Search for the keyword locally
        # search_locally('Police')

        # Search using Azure Search
        search_manager = SearchManager("video-analyzer-search", "2017-11-11", 'https://video-analyzer-search.search.windows.net',
                                       '40BCFD3875D09243AB49A3175FE9AD99')
        search_manager.create_data_source(Constants.SEARCH_DATASOURCE_NAME_DEFAULT, "AccountEndpoint=https://video-analyzer-db.documents.azure.com:443/;AccountKey=VREFPwEbkjNwRji7XaIjbauu2ElUc9TBgEWQsJ4OnuYJYPuHUlfD1Ru2zprjQRvKHWCouxDIbbMAt06tXKk8kA==;Database=" + str(db_frames['id']),
                                          str(collection_frames['id']), None)
        search_manager.create_index(Constants.SEARCH_INDEX_NAME_DEFAULT)
        search_manager.create_indexer(Constants.SEARCH_INDEXER_NAME_DEFAULT, Constants.SEARCH_DATASOURCE_NAME_DEFAULT, Constants.SEARCH_INDEX_NAME_DEFAULT)
        search_manager.run_indexer(Constants.SEARCH_INDEXER_NAME_DEFAULT)
        search_manager.get_indexer_status(Constants.SEARCH_INDEXER_NAME_DEFAULT)

        response = search_manager.search(Constants.SEARCH_INDEX_NAME_DEFAULT, "car")
        print(response.json())

        end = time.time()
        print('Ending: ' + str(end) + '\n')
        print('Time elapsed: ' + str(end - start) + '\n')
    except Exception as e:
        print(e.args)





