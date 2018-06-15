import cv2 as cv
import numpy as np
import moviepy.editor as mp
import os
import requests
import collections
import functools
import matplotlib.pyplot as plt
from azure.storage.blob import BlockBlobService, PublicAccess
from concurrent import futures
from wordcloud import WordCloud
from Models import *
from Utility import *


# A helper class to upload and download files on an Azure Blob Storage
class BlobManager(object):
    def __init__(self, account_name, account_key):
        self.block_blob_service = BlockBlobService(account_name=account_name, account_key=account_key)

    def create_container(self, container_name):
        containers = self.block_blob_service.list_containers()
        for container in containers:
            if container.name == container_name:
                return
        self.block_blob_service.create_container(container_name)
        # Set permission as public
        self.block_blob_service.set_container_acl(container_name, public_access=PublicAccess.Container)

    def upload(self, filename, container_name):
        full_file_path = os.path.join(os.getcwd(), filename)
        self.block_blob_service.create_blob_from_path(container_name, filename, full_file_path)

    def download(self, path, filename, container_name):
        full_file_path = os.path.join(path, str.replace(filename, '.', '_Downloaded.'))
        self.block_blob_service.get_blob_to_path(container_name, filename, full_file_path)

    def list_blobs(self, container_name):
        return self.block_blob_service.list_blobs(container_name)

    def get_blob_url(self, container_name, blob_name):
        return self.block_blob_service.make_blob_url(container_name, blob_name)

    def delete_container(self, container_name):
        self.block_blob_service.delete_container(container_name)

    def delete_blob(self, container_name, blob_name):
        self.block_blob_service.delete_blob(container_name, blob_name)

    def clear(self):
        containers = self.block_blob_service.list_containers()
        for container in containers:
            self.delete_container(container.name)


# A helper class that can extract audio/frames from a video
class VideoManager(object):
    def __init__(self, path, blob_manager):
        if not os.path.exists(path):
            os.makedirs(path)
        self.curr_dir = path
        self.blob = blob_manager

    def grab_frames(self, filename, start_time, end_time, grab_rate_type, grab_rate):

        # Handle invalid input
        clip = self.handle_invalid_input(end_time, filename, grab_rate, grab_rate_type, start_time)

        # Cut the videofile to desired range
        clipped_filename = self.clip_video(start_time, end_time, filename, clip)

        # Grab frames based on preset grabRate
        cap = cv.VideoCapture(clipped_filename)
        fpms = float(cap.get(cv.CAP_PROP_FPS)) / 1000
        success, image = cap.read()
        current_frame_index = 0
        grabbed_frame_count = 0
        frame_list = []
        while success:
            # Capture image
            success, image = cap.read()

            # Create a VideoFrame and save as file according to grabRate
            current_video_time = int(current_frame_index / fpms)
            condition = current_frame_index % grab_rate == 0 if grab_rate_type == GrabRateType.BY_FRAME else int(
                current_video_time / grab_rate) > grabbed_frame_count

            if condition:
                grabbed_frame_count += 1
                frame = VideoFrame(image, current_video_time + start_time * 1000, current_frame_index)
                frame_list.append(frame)
                self.generate_image_file(filename, grabbed_frame_count, frame)
            current_frame_index += 1

        cap.release()
        return frame_list

    def handle_invalid_input(self, end_time, filename, grab_rate, grab_rate_type, start_time):
        try:
            clip = mp.VideoFileClip(os.path.join(self.curr_dir + filename))
        except FileNotFoundError:
            raise InvalidInputException(Messages.FILE_NOT_FOUND.value)
        if start_time < 0 or end_time <= start_time or end_time > clip.duration or start_time >= end_time or int(
                start_time) != start_time or int(end_time) != end_time:
            raise InvalidInputException(Messages.INVALID_START_END_TIME.value)
        if int(grab_rate) != grab_rate or grab_rate < 0 or (
                grab_rate_type == GrabRateType.BY_SECOND and grab_rate > clip.duration * 1000):
            raise InvalidInputException(Messages.INVALID_GRAB_RATE.value)
        return clip

    def clip_video(self, start_time, end_time, filename, clip):
        clipped = clip.subclip(start_time, end_time)
        clipped_filename = os.path.join(self.curr_dir, str.replace(filename, '.', '_Clipped.'))
        clipped.write_videofile(clipped_filename)
        return clipped_filename

    # Generate file and save as jpg file
    def generate_image_file(self, filename, index, frame):
        frame_std_time = ms_to_std_time(frame.video_time)
        filename = self.generate_frame_filename(filename, index, frame_std_time)
        print('Generating...' + filename)
        cv.imwrite(filename, frame.image)
        self.blob.upload(filename, 'image')

    def generate_frame_filename(self, filename, index, frame_std_time):
        return os.path.splitext(self.curr_dir + filename)[0] + str(index) + '_' + frame_std_time + '.jpg'

    def grab_audio(self, filename):
        clip = mp.VideoFileClip(os.path.join(self.curr_dir, filename))
        audio_filename = self.generate_audio_filename(filename)
        clip.audio.write_audiofile(audio_filename)
        self.blob.upload(audio_filename, 'audio')

    def generate_audio_filename(self, filename):
        return os.path.splitext(self.curr_dir + filename)[0] + '_Audio.mp3'


class ImageAnalyzer(object):
    def __init__(self, subscription_key, vision_base_url, dir):
        self.subscription_key = subscription_key
        self.vision_base_url = vision_base_url
        self.vision_analyze_url = vision_base_url + "analyze"
        self.dir = dir

    # Analyze an image from local upload
    def analyze_local(self, image_filename):
        assert self.subscription_key
        path = os.path.join(self.dir, image_filename)

        # Read the image into a byte array
        image_data = open(path, "rb").read()
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key,
                   'Content-Type': 'application/octet-stream'}
        params = {'visualFeatures': 'Categories,Description,Color'}
        response = requests.post(self.vision_analyze_url, headers=headers,
                                 params=params, data=image_data)
        response.raise_for_status()
        analysis = response.json()
        return analysis

    # Analyze an image from a url
    def analyze_remote(self, image_url):
        assert self.subscription_key
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        params = {'visualFeatures': 'Categories,Description,Color'}
        data = {'url': image_url}
        response = requests.post(self.vision_analyze_url, headers=headers, params=params, json=data)
        response.raise_for_status()

        # The 'analysis' object contains various fields that describe the image
        analysis = response.json()
        return analysis

    # Analyse images concurrently
    def analyze_remote_by_batch(self, urls):
        with futures.ThreadPoolExecutor(max_workers=3) as executor:
            async_tasks = map(lambda x: executor.submit(self.analyze_remote, x), urls)
            analyses = []
            for future in futures.as_completed(async_tasks):
                analyses.append(future.result())
            return analyses

    def convert_to_image_data(self, analysis_json):
        categories = map(lambda x: (x["name"], x["score"]), analysis_json["categories"])
        tags = analysis_json["description"]["tags"]
        captions = map(lambda x: (x["text"], x["confidence"]), analysis_json["description"]["captions"])
        dominant_colors = analysis_json["color"]["dominantColors"]
        foreground_color = analysis_json["color"]["dominantColorForeground"]
        background_color = analysis_json["color"]["dominantColorBackground"]
        accent_color = analysis_json["color"]["accentColor"]
        isBwImg = analysis_json["color"]["isBwImg"]
        height = analysis_json["metadata"]["height"]
        width = analysis_json["metadata"]["width"]
        image_format = analysis_json["metadata"]["format"]
        request_id = analysis_json["requestId"]

        return ImageData(categories, tags, captions, dominant_colors, foreground_color,
                         background_color, accent_color, isBwImg, height, width, image_format, request_id)


# Main Execution Body
if __name__ == '__main__':
    blob = BlobManager(account_name='videoanalyserstorage',
                       account_key='0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w==')
    # blob.clear()
    clear_local_files('./data/')
    blob.create_container('video')
    blob.create_container('image')
    blob.create_container('audio')
    try:
        grabber = VideoManager('./data/', blob)
        # Obtain a list of frames
        frame_list = grabber.grab_frames('Suntec.mp4', 100, 101, GrabRateType.BY_SECOND, 400)

        # grabber.grab_audio("Suntec.mp4")
    except Exception as e:
        print(e.args)

    # Obtain a list of analyses based on the grabbed frames
    image_analyzer = ImageAnalyzer("c49f0b5b59654ca28e3fec02d015c60f",
                                   "https://southeastasia.api.cognitive.microsoft.com/vision/v1.0/", "./data/")
    urls = map(lambda x: blob.get_blob_url('image', x.name), blob.list_blobs('image'))
    analyses = image_analyzer.analyze_remote_by_batch(urls)
    image_data_list = map(lambda x: image_analyzer.convert_to_image_data(x), analyses)
    frame_to_data_list = list(zip(frame_list, image_data_list))
    for frame, image_data in frame_to_data_list:
        frame.set_image_data(image_data)
    video_data = VideoData(frame_list)
    top_keywords = video_data.top_keywords_from_frames(8)
    font_path = 'Symbola.ttf'
    text = ' '.join(video_data.get_all_tags())
    word_cloud = WordCloud(background_color="white", font_path=font_path).generate_from_frequencies(dict(top_keywords))
    word_cloud.to_file('Suntec_word_cloud.jpg')






