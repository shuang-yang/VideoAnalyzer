import cv2 as cv
import numpy as np
import moviepy.editor as mp
import os
import requests
import collections
import functools
import json
import time
import matplotlib.pyplot as plt
from enum import Enum
from azure.storage.blob import BlockBlobService, PublicAccess
from concurrent import futures
from wordcloud import WordCloud
from Models import *
from Utility import *
from Analyzers import *
from DataSourceManagers import *

CONFIDENCE_THRESHOLD = 0.5


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


def analyze_frames(blob, frame_list, image_analyzer):
    # Obtain a list of analyses based on the grabbed frames
    urls = list(map(lambda x: blob.get_blob_url('image', x.name), blob.list_blobs('image')))
    analyses = image_analyzer.analyze_remote_by_batch(urls)
    # Print json information to file
    output_file = open("Output_image_json.txt", "w")
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

    # print tags text to file
    outputtags_file = open("Output_tags.txt", "w")
    for frame, image_data in frame_to_data_list:
        frame.set_image_data(image_data)
        # print('Frame ' + str(frame.index) + ' categories: ' + str([c[0] for c in image_data.categories]))
        print('Frame at: ' + str(frame.video_time) + '\nTags: \n' + str(image_data.tags))
        outputtags_file.write('Frame at: ' + ms_to_std_time(frame.video_time) + '\n tags: \n' + str(image_data.tags) + '\n\n')
        if len(image_data.captions) != 0:
            caption = str(image_data.captions[0][0])
            print('Frame ' + str(frame.index) + ' captions: ' + caption)
    outputtags_file.close()


def analyze_faces(blob, frame_list, face_analyzer):
    # Obtain a list of analyses based on the grabbed frames
    urls = map(lambda x: blob.get_blob_url('image', x.name), blob.list_blobs('image'))
    analyses = face_analyzer.analyze_remote_by_batch(urls)
    # print json info to file
    output_file = open("Output_faces_json.txt", "w")
    for analysis in analyses:
        json.dump(analyses, output_file)
    output_file.close()
    # Add Image analyses result to frames
    face_data_lists = map(lambda x: face_analyzer.convert_to_face_data(x), analyses)
    frame_to_face_data_list = list(zip(frame_list, face_data_lists))
    for frame, face_data_list in frame_to_face_data_list:
        frame.set_face_data_list(face_data_list)
        print('Frame ' + str(frame.index) + ' faces: ')
        for face in face_data_list:
            print(" face " + str(face.id))

# Main Execution Body
if __name__ == '__main__':
    start = time.time()
    print('Starting: ' + str(start) + '\n')
    blob = create_blob_manager()
    clear_local_files('./data/')

    try:
        grabber = VideoManager('./data/', blob)
        # Obtain a list of frames
        frame_list = grabber.grab_frames('Friends101.mkv', 300, 400, GrabRateType.BY_SECOND, 5000)
        # grabber.grab_audio("Suntec.mp4")

        image_analyzer = ImageAnalyzer("c49f0b5b59654ca28e3fec02d015c60f",
                                       "https://southeastasia.api.cognitive.microsoft.com/vision/v1.0/", "./data/")
        face_analyzer = FaceAnalyzer("7854c9ad29294ce89d2142ac0977b194",
                                     "https://southeastasia.api.cognitive.microsoft.com/face/v1.0/detect", "./data/")

        analyze_frames(blob, frame_list, image_analyzer)
        # analyze_faces(blob, frame_list, face_analyzer)

        # Add frames with data to video_data
        video_data = VideoData(frame_list)
        print(video_data.get_captions_as_text())
        # print caption text to file
        output_file = open("Output_captions.txt", "w")
        output_file.write(video_data.get_captions_as_text())
        output_file.close()

        # generate_word_clouds_from_frames(video_data)
        end = time.time()
        print('Ending: ' + str(end) + '\n')
        print('Time elapsed: ' + str(end - start) + '\n')
    except Exception as e:
        print(e.args)





