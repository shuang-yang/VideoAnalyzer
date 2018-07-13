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
from Models import *
from Utility import *
from Analyzers import *


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

    def clear_container(self, container_name):
        blobs = self.list_blobs(container_name)
        for blob in blobs:
            self.delete_blob(container_name, blob.name)

    def delete_blob(self, container_name, blob_name):
        self.block_blob_service.delete_blob(container_name, blob_name)

    def clear(self):
        containers = self.block_blob_service.list_containers()
        for container in containers:
            self.clear_container(container.name)


# A helper class that can extract audio/frames from a video
class VideoManager(object):
    def __init__(self, path, blob_manager):
        if not os.path.exists(path):
            os.makedirs(path)
        self.curr_dir = path
        self.blob = blob_manager

    # Obtain a list of frames with given parameters
    def grab_frames(self, filename, start_time, end_time, grab_rate_type, grab_rate):

        # Handle invalid input
        clip = self.handle_invalid_input(end_time, filename, grab_rate, grab_rate_type, start_time)

        # Cut the videofile to desired range
        # clipped_filename = self.clip_video(start_time, end_time, filename, clip)

        # Grab frames based on preset grabRate
        filepath = os.path.join(self.curr_dir, filename)
        cap = cv.VideoCapture(filepath)
        fpms = float(cap.get(cv.CAP_PROP_FPS)) / 1000
        success, image = cap.read()
        current_frame_index = 0
        grabbed_frame_count = 0
        frame_list = []

        while success and cap.get(cv.CAP_PROP_POS_MSEC) < start_time * 1000:
            success, image = cap.read()
        while success and cap.get(cv.CAP_PROP_POS_MSEC) < end_time * 1000:
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
        clipped.write_videofile(clipped_filename, codec='libx264')
        return clipped_filename

    # Generate file and save as jpg file
    def generate_image_file(self, filename, index, frame):
        frame_std_time = ms_to_std_time(frame.video_time)
        filename = self.generate_frame_filename(filename, index, frame_std_time)
        print('Generating...' + filename)
        cv.imwrite(filename, frame.image)
        self.blob.upload(filename, 'image')
        frame.set_url(self.blob.get_blob_url('image', filename))
        frame.set_filename(filename)

    def generate_frame_filename(self, filename, index, frame_std_time):
        return os.path.splitext(self.curr_dir + filename)[0] + '_' + frame_std_time + '_' + str(index) + '.jpg'

    def grab_audio(self, filename):
        clip = mp.VideoFileClip(os.path.join(self.curr_dir, filename))
        audio_filename = self.generate_audio_filename(filename)
        clip.audio.write_audiofile(audio_filename)
        self.blob.upload(audio_filename, 'audio')

    def generate_audio_filename(self, filename):
        return os.path.splitext(self.curr_dir + filename)[0] + '_Audio.mp3'

