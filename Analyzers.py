import os
import requests
import json
import time
from enum import Enum
from Models import *
from Utility import *
from DataSourceManagers import *


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
        # with futures.ThreadPoolExecutor() as executor:
            #
            # async_tasks = map(lambda x: executor.submit(self.analyze_remote, x), urls)
            # analyses = []
            # for future in futures.as_completed(async_tasks):
            #     print(future.result())
            #     analyses.append(future.result())
            # return analyses
            # index = 0
            # analyses = []
            # while index < len(urls):
            #     async_tasks = []
            #     num = len(urls) - index if len(urls) - index < 10 else 10
            #     for i in range(num):
            #         async_tasks.append(executor.submit(self.analyze_remote(urls[index + i])))
            #     time.sleep(1)
            #     for future in futures.as_completed(async_tasks):
            #         print(future.result())
            #         analyses.append(future.result())
            #     index += 10
            # return analyses
        analyses = []
        for url in urls:
            analysis = self.analyze_remote(url)
            analyses.append(analysis)
        return analyses

    # Converts a json-formated string into an ImageData object
    def convert_to_image_data(self, analysis_json):
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
    def __init__(self, subscription_key, face_api_url, dir):
        self.subscription_key = subscription_key
        self.face_api_url = face_api_url
        self.dir = dir

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
        with futures.ThreadPoolExecutor() as executor:
            async_tasks = map(lambda x: executor.submit(self.analyze_remote, x), urls)
            analyses = []
            for future in futures.as_completed(async_tasks):
                print(future.result())
                analyses.append(future.result())
            return analyses

    # Converts a json-formated string into a list of FaceData object
    def convert_to_face_data(self, analysis_json):
        face_data_list = []
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

    def analyze_local(self, image_filename, service):
        assert self.subscription_key
        path = os.path.join(self.dir, image_filename)
        text_analytics_url = self.text_analytics__base_url + service

        # Read the image into a byte array
        text_data = open(path, "rb").read()
        data = {'documents': [
                  {'id': '1', 'language': 'en', 'text': 'a person holding a sign. a man holding a sign. a man standing in a kitchen. David Schwimmer in a red shirt standing in front of a window. a person standing in a room. a group of people standing in a kitchen. a group of people standing in a room playing a video game. a man standing in front of a mirror posing for the camera. a man standing next to a woman. a man holding a phone. a man standing next to a window. a couple of people that are standing in a room. a couple of people that are standing in a room. a group of people looking at a laptop. a man and a woman sitting at a table eating food. a man and a woman sitting at a table. a group of people sitting at a table. a man and a woman sitting at a table. a group of people sitting at a table. a man and a woman sitting at a table. a group of people sitting at a table. a man and a woman sitting at a table. a man and a woman looking at the camera. a man and a woman looking at the camera. a man and a woman sitting at a table. a group of people sitting at a table. a group of people sitting at a table. Courteney Cox et al. sitting at a table. Madeline Zima sitting on a bed. a woman sitting on a bed. a woman sitting on a bed. a woman sitting on a bed. David Schwimmer standing in front of a mirror posing for the camera. a person standing in front of a mirror posing for the camera. a man and a woman standing in a kitchen. a person standing in a room. a man playing a video game. a person sitting in a room. David Schwimmer standing in front of a building. a man sitting in front of a building. a person sitting in front of a fence. a person sitting in a room. a person in a dark room. a woman sitting in a dark room. a close up of a bridge. a person sitting on a kitchen counter. a group of people sitting at a table. a person sitting at a table. a person wearing a suit and tie. a person sitting at a table. a person cutting a cake. a person standing in a room. a person standing in a room. a group of people sitting at a table. a man standing in front of a mirror. a group of people sitting at a table in a restaurant. a man and a woman standing in front of a door. a person standing in front of a mirror posing for the camera. a man and a woman looking at the camera. '
                   }
                ]}
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}
        response = requests.post(text_analytics_url,
                                 headers=headers, json=data)
        response.raise_for_status()
        analysis = response.json()
        return analysis