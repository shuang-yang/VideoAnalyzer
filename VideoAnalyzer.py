import cv2 as cv
import numpy as np
import moviepy.editor as mp
import subprocess
import os
import datetime
from enum import Enum
from azure.storage.blob import BlockBlobService, PublicAccess


# Utility classes
class VideoFrame(object):
    def __init__(self, image, video_time, index):
        self.image = image
        self.video_time = video_time
        self.index = index


class GrabRateType(Enum):
    BY_FRAME = 0
    BY_SECOND = 1


# Utility methods
def ms_to_std_time(time_in_ms):
    time_in_s = int(time_in_ms / 1000)
    ms_component = get_ms_component(time_in_ms)
    std_time_in_s = time_in_s % 60
    std_time_in_s_str =  str(std_time_in_s) if std_time_in_s >= 10 else '0' + str(std_time_in_s)
    std_time_in_min = int((time_in_s - std_time_in_s) % 3600 / 60)
    std_time_in_min_str = str(std_time_in_min) if std_time_in_min >= 10 else '0' + str(std_time_in_min)
    std_time_in_hr = int((time_in_s - std_time_in_min * 60 - std_time_in_s) / 3600)
    std_time_in_hr_str = str(std_time_in_hr) if std_time_in_hr >= 10 else '0' + str(std_time_in_hr)
    std_time = std_time_in_hr_str + ':' + std_time_in_min_str + ':' + std_time_in_s_str + '.' + ms_component
    return std_time


def get_ms_component(time_in_ms):
    ms_component = str(time_in_ms)[-3:] if time_in_ms >= 100 else str(time_in_ms)
    while len(ms_component) < 3:
        ms_component = '0' + ms_component
    return ms_component


def clear_local_files(path):
    files = os.listdir(path)
    for file in files:
        if '.mp4' not in file:
            file_path = os.path.join(path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)


# A helper class to upload and download files on an Azure Blob Storage
class BlobManager(object):
    def __init__(self, account_name, account_key):
        self.block_blob_service = BlockBlobService(account_name=account_name, account_key=account_key)

    def create_container(self, container_name):
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
        self.curr_dir = path
        self.blob = blob_manager

    def grab_frames(self, filename, start_time, end_time, grab_rate_type, grab_rate):
        # Cut the videofile to desired range
        clipped_filename = self.clip_video(start_time, end_time, filename)

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
            condition = current_frame_index % grab_rate == 0 if grab_rate_type == GrabRateType.BY_FRAME else int(current_video_time / grab_rate) > grabbed_frame_count

            if condition:
                grabbed_frame_count += 1
                frame = VideoFrame(image, current_video_time + start_time * 1000, current_frame_index)
                frame_list.append(frame)
                self.generate_image_file(filename, grabbed_frame_count, frame)
            current_frame_index += 1

        cap.release()
        return frame_list

    def clip_video(self, start_time, end_time, filename):
        clip = mp.VideoFileClip(os.path.join(self.curr_dir + filename)).subclip(start_time, end_time)
        clipped_filename = os.path.join(self.curr_dir, str.replace(filename, '.', '_Clipped.'))
        clip.write_videofile(clipped_filename)
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


# Main Execution Body
if __name__ == '__main__':
    blob = BlobManager(account_name='videoanalyserstorage',
                       account_key='0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w==')
    blob.clear()
    clear_local_files('./data/')
    blob.create_container('video')
    blob.create_container('image')
    blob.create_container('audio')
    grabber = VideoManager('./data/', blob)
    frame_list = grabber.grab_frames('Suntec.mp4', 100, 101, GrabRateType.BY_SECOND, 200)
    # grabber.grab_audio("Suntec.mp4")








