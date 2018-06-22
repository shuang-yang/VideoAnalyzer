import collections
import operator
from collections import Counter
from wordcloud import WordCloud


class VideoFrame(object):
    def __init__(self, image, video_time, index, image_data=None, face_data_list=None):
        self.image = image
        self.video_time = video_time
        self.index = index
        self.image_data = image_data
        self.face_data_list = face_data_list

    def set_image_data(self, image_data):
        self.image_data = image_data

    def set_face_data_list(self, face_data_list):
        self.face_data_list = face_data_list

    def get_predominant_emotions(self, num):
        all_emotions = []
        for face in self.face_data_list:
            # emotion = max(face.emotions.iteritems(), key=operator.itemgetter(1))[0]
            emotion = max(face.emotions, key=face.emotions.get)
            all_emotions.append(emotion)
        counter = collections.Counter(all_emotions)
        return counter.most_common(num)


class VideoData(object):
    def __init__(self, frames_with_data, audio_data=None):
        self.frames_with_data = frames_with_data
        self.audio_data = audio_data

    def top_keywords_from_frames(self, num):
        counter = collections.Counter(self.get_all_tags())
        top_keywords = counter.most_common(num)
        return top_keywords

    def top_caption_keywords_from_frames(self, num):
        counter = collections.Counter(self.get_all_caption_keywords())
        return counter.most_common(num)

    def get_all_tags(self):
        tags_list = []
        for frame in self.frames_with_data:
            tags = frame.image_data.tags
            if tags is not None:
                tags_list.extend(tags)
            else:
                continue
        return tags_list

    # Get all captions of the frames condensed in one text
    def get_captions_as_text(self):
        caption = ""
        for frame in self.frames_with_data:
            # If the caption list is not empty, add them to the caption string
            if len(frame.image_data.captions) != 0:
                frame_caption = frame.image_data.captions[0][0]
                caption += frame_caption + ". "
        return caption

    def get_all_caption_keywords(self):
        caption_keywords_list = []
        for frame in self.frames_with_data:
            if len(frame.image_data.captions) != 0:
                caption = frame.image_data.captions[0][0]
                caption_keywords_list.extend(caption.split())
            else:
                continue
        return caption_keywords_list


class ImageData(object):
    def __init__(self, categories, tags, captions, dominant_colors, foreground_color,
                 background_color, accent_color, isBwImg, height, width, image_format, request_id, landmarks=[], celebrities=[]):
        self.categories = categories
        self.tags = tags
        self.captions = captions
        self.dominant_colors = dominant_colors
        self.foreground_color = foreground_color
        self.background_color = background_color
        self.accent_color = accent_color
        self.isBwImg = isBwImg
        self.height = height
        self.width = width
        self.image_format = image_format
        self.request_id = request_id
        self.landmarks = landmarks
        self.celebrities = celebrities


class FaceData(object):
    def __init__(self, id, rectangle, smile, head_pose, gender, age, facial_hair, glasses,
                    emotions, blur, exposure, noise, makeup, accessories, occlusion, bald, hair_colors):
        self.id = id
        self.rectangle = rectangle
        self.smile = smile
        self.head_pose = head_pose
        self.gender = gender
        self.age = age
        self.facial_hair = facial_hair
        self.glasses = glasses
        self.emotions = emotions
        self.blur = blur
        self.exposure = exposure
        self.noise = noise
        self.makeup = makeup
        self.accessories = accessories
        self.occlusion = occlusion
        self.bald = bald
        self.hair_colors = hair_colors

