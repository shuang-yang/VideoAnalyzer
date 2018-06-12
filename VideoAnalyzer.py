import cv2 as cv
import numpy as np
import moviepy.editor as mp
import subprocess
import os
import datetime
from azure.storage.blob import BlockBlobService, PublicAccess


class VideoFrame(object):
    def __init__(self, image, timestamp, index):
        self.image = image
        self.timestamp = timestamp
        self.index = index


# A helper class to upload and download files on an Azure Blob Storage
class BlobStorer(object):
    def __init__(self, account_name, account_key):
        self.block_blob_service = BlockBlobService(account_name=account_name, account_key=account_key)

    def create_container(self, container_name):
        self.block_blob_service.create_container(container_name)
        # Set permission as public
        self.block_blob_service.set_container_acl(container_name, public_access=PublicAccess.Container)

    def upload(self, filename, container_name):
        full_file_path = os.path.join(os.getcwd(), filename)
        self.block_blob_service.create_blob_from_path(container_name, filename, full_file_path)

    def download(self, filename, container_name):
        full_file_path = os.path.join(os.getcwd(), str.replace(filename, '.', '_Downloaded.'))
        self.block_blob_service.get_blob_to_path(container_name, filename, full_file_path)

    def list_blobs(self, container_name):
        generator = self.block_blob_service.list_blobs(container_name)
        for contained_blob in generator:
            print("\t Blob name: " + contained_blob.name)

    def delete_container(self, container_name):
        self.block_blob_service.delete_container(container_name)

    def delete_blob(self, container_name, blob_name):
        self.block_blob_service.delete_blob(container_name, blob_name)


# A helper class that can extract audio/frames from a video
class VideoGrabber(object):
    def __init__(self, path):
        self.curr_dir = path

    def grab_frames(self, filename, grab_rate):

        # Grab frames based on preset grabRate
        cap = cv.VideoCapture(self.curr_dir + filename)
        success, image = cap.read()
        current_frame_index = 0
        frame_list = []
        while success:
            # Capture image
            success, image = cap.read()

            # Create a VideoFrame and save as file according to grabRate
            if current_frame_index % grab_rate == 0:
                timestamp = datetime.datetime.now()
                frame = VideoFrame(image, timestamp, current_frame_index)
                frame_list.append(frame)
                self.generate_image_file(filename, current_frame_index, image)

            current_frame_index += 1

        cap.release()
        return frame_list

    # Generate file and save as jpg file
    def generate_image_file(self, filename, index, image):
        filename = self.generate_frame_filename(filename, index)
        print('Generating...' + filename)
        cv.imwrite(filename, image)
        blob.upload(filename, 'image')

    def generate_frame_filename(self, filename, index):
        return os.path.splitext(self.curr_dir + filename)[0] + str(index) + '.jpg'

    def grab_audio(self, input_file_name, output_file_name):
        clip = mp.VideoFileClip(input_file_name)
        clip.audio.write_audiofile(output_file_name)
        blob.upload(output_file_name, 'audio')

# Main Execution Body
if __name__ == '__main__':
    blob = BlobStorer(account_name='videoanalyserstorage',
                      account_key='0GALSGQ2WZgu4tuH4PWKAM85K3KzhbhsAHulCcQndOcW0EgJ1BaP10D6KBgRDOCJQcz3B9AAPkOY6F/mYhXa7w==')
    blob.create_container('video')
    blob.create_container('image')
    blob.create_container('audio')
    # blob.upload('Suntec.mp4', 'video')
    # blob.download('Suntec.mp4', 'video')
    grabber = VideoGrabber('./')
    frame_list = grabber.grab_frames('Suntec.mp4', 1000)
    grabber.grab_audio("Suntec.mp4", "SuntecAudio.mp3")






