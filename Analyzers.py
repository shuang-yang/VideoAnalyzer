import os
import requests
import json
import time
from concurrent import futures
from enum import Enum
from Models import *
from Utility import *
from DataSourceManagers import *


class ImageAnalyzer(object):
    def __init__(self, subscription_key, vision_base_url, dir, max_calls_per_second):
        self.subscription_key = subscription_key
        self.vision_base_url = vision_base_url
        self.vision_analyze_url = vision_base_url + "analyze"
        self.dir = dir
        self.max_calls_per_second = max_calls_per_second

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
        index = 0
        analyses = []
        async_tasks = []
        max_call = self.max_calls_per_second
        # Submit tasks concurrently, with a given maximum number of calls/second
        while index < len(urls):
            # Submit max_call number of api calls per second
            num = len(urls) - index if len(urls) - index < max_call else max_call
            with futures.ThreadPoolExecutor() as executor:
                batch_tasks = list(map(lambda x: executor.submit(self.analyze_remote, urls[index + x]), range(num)))
                async_tasks.extend(batch_tasks)
                time.sleep(1)
                print("Image Analyzer Concurrency: Submitted batch " + str(index / 10))
                index += max_call

        # Add result of analysis in the order of submission
        for async_task in async_tasks:
            if async_task.exception() is not None:
                print('generated an exception: %s' % (async_task.exception()))
            else:
                analyses.append(async_task.result())

        return analyses

    # Converts a json-formated string into an ImageData object
    def convert_to_image_data(self, analysis_json):
        if len(analysis_json) == 0:
            return None
        categories = map(lambda x: (x["name"], x["score"]), analysis_json["categories"])
        tags = analysis_json["description"]["tags"]

        # Obtain captions information
        caption_result = analysis_json["description"]["captions"]
        captions = []
        for result in caption_result:
            captions.append((result["text"], result["confidence"]))

        dominant_colors = analysis_json["color"]["dominantColors"]
        foreground_color = analysis_json["color"]["dominantColorForeground"]
        background_color = analysis_json["color"]["dominantColorBackground"]
        accent_color = analysis_json["color"]["accentColor"]
        isBwImg = analysis_json["color"]["isBwImg"]
        height = analysis_json["metadata"]["height"]
        width = analysis_json["metadata"]["width"]
        image_format = analysis_json["metadata"]["format"]
        request_id = analysis_json["requestId"]

        # Optional landmark and celebrity identification
        details = []
        for category in analysis_json["categories"]:
            if category.get("detail") is not None:
                details.append(category["detail"])
        landmarks = []
        celebrities = []
        for detail in details:
            print('considering detail')
            if detail.get("landmarks") is not None:
                for landmark in detail["landmarks"]:
                    landmarks.append((landmark["name"], landmark["confidence"]))
            if detail.get("celebrities") is not None:
                for celebrity in detail["celebrities"]:
                    celebrities.append((celebrity["name"], celebrity["confidence"], celebrity["faceRectangle"]))

        return ImageData(categories, tags, captions, dominant_colors, foreground_color,
                         background_color, accent_color, isBwImg, height, width, image_format, request_id, landmarks, celebrities)


class FaceAnalyzer(object):
    def __init__(self, subscription_key, face_api_url, dir, max_calls_per_second):
        self.subscription_key = subscription_key
        self.face_api_url = face_api_url
        self.dir = dir
        self.max_calls_per_second = max_calls_per_second

    def analyze_local(self, image_filename):
        assert self.subscription_key
        path = os.path.join(self.dir, image_filename)

        # Read the image into a byte array
        image_data = open(path, "rb").read()
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key,
                   'Content-Type': 'application/octet-stream'}
        params = {'returnFaceId': 'true',
                  'returnFaceLandmarks': 'false',
                  'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,' +
                  'emotion,hair,makeup,occlusion,accessories,blur,exposure,noise'}
        response = requests.post(self.face_api_url,
                                 params=params, headers=headers, data=image_data)
        response.raise_for_status()
        analysis = response.json()
        return analysis

    def analyze_remote(self, image_url):
        assert self.subscription_key
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        params = {'returnFaceId': 'true',
                  'returnFaceLandmarks': 'false',
                  'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,' +
                  'emotion,hair,makeup,occlusion,accessories,blur,exposure,noise'}
        data = {'url': image_url}
        response = requests.post(self.face_api_url, params=params, headers=headers,  json=data)
        response.raise_for_status()

        # The 'analysis' object contains various fields that describe the image
        analysis = response.json()
        return analysis

    # Analyse faces concurrently
    def analyze_remote_by_batch(self, urls):
        index = 0
        analyses = []
        async_tasks = []
        max_call = self.max_calls_per_second
        # Submit tasks concurrently, with a given maximum number of calls/second
        while index < len(urls):
            # Submit max_call number of api calls per second
            num = len(urls) - index if len(urls) - index < max_call else max_call
            with futures.ThreadPoolExecutor() as executor:
                batch_tasks = list(map(lambda x: executor.submit(self.analyze_remote, urls[index + x]), range(num)))
                async_tasks.extend(batch_tasks)
                time.sleep(1)
                print("Face Analyzer Concurrency: Submitted batch " + str(index / max_call))
                index += max_call

        # Add result of analysis in the order of submission
        for async_task in async_tasks:
            if async_task.exception() is not None:
                print('generated an exception: %s' % (async_task.exception()))
            else:
                analyses.append(async_task.result())

        return analyses

    # Converts a json-formated string into a list of FaceData object
    def convert_to_face_data(self, analysis_json):
        face_data_list = []
        if len(analysis_json) == 0:
            return face_data_list
        for face_json in analysis_json:
            print("analyzing face...")
            id = face_json["faceId"]
            rectangle = face_json["faceRectangle"]
            attributes = face_json["faceAttributes"]
            smile = attributes["smile"]
            head_pose = attributes["headPose"]
            gender = attributes["gender"]
            age = attributes["age"]
            facial_hair = attributes["facialHair"]
            glasses = attributes["glasses"]
            emotions = attributes["emotion"]
            blur = attributes["blur"]
            exposure = attributes["exposure"]
            noise = attributes["noise"]
            makeup = attributes["makeup"]
            accessories = attributes["accessories"]
            occlusion = attributes["occlusion"]
            hair = attributes["hair"]
            bald = hair["bald"]
            hair_colors = []
            for color in hair["hairColor"]:
                hair_colors.append((color["color"], color["confidence"]))
            face_data = FaceData(id, rectangle, smile, head_pose, gender, age, facial_hair, glasses,
                                 emotions, blur, exposure, noise, makeup, accessories, occlusion, bald, hair_colors)
            face_data_list.append(face_data)

        return face_data_list


class TextAnalyticsService(Enum):
    LANGUAGES = "languages"
    SENTIMENT = "sentiment"
    KEY_PHRASES = "keyPhrases"
    ENTITIES = "entities"


class TextAnalyzer(object):
    def __init__(self, subscription_key, text_analytics__base_url, dir):
        self.subscription_key = subscription_key
        self.text_analytics__base_url = text_analytics__base_url
        self.dir = dir

    def analyze_local(self, filename, service):
        assert self.subscription_key
        path = os.path.join(self.dir, filename)
        text_analytics_url = self.text_analytics__base_url + service

        # Read the image into a byte array
        # text_data = open(path, "rb").read()
        with open(path, 'r') as myfile:
            text_data = myfile.read().replace('\n', '')
        data = {'documents': [
                  {'id': '1', 'language': 'en', 'text': text_data}
                ]}
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        response = requests.post(text_analytics_url,
                                 headers=headers, json=data)
        response.raise_for_status()
        analysis = response.json()
        return analysis