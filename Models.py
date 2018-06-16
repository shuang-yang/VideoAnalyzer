import collections
from wordcloud import WordCloud


class VideoFrame(object):
    def __init__(self, image, video_time, index, image_data=None):
        self.image = image
        self.video_time = video_time
        self.index = index
        self.image_data = image_data

    def set_image_data(self, image_data):
        self.image_data = image_data


class VideoData(object):
    def __init__(self, frames_with_data, face_data=None, audio_data=None):
        self.frames_with_data = frames_with_data
        self.face_data = face_data
        self.audio_data = audio_data

    def top_keywords_from_frames(self, num):
        counter = collections.Counter(self.get_all_tags())
        top_keywords = counter.most_common(num)
        return top_keywords

    def get_all_tags(self):
        tags_list = []
        for frame in self.frames_with_data:
            tags_list.extend(frame.image_data.tags)
        return tags_list


class ImageData(object):
    def __init__(self, categories, tags, captions, dominant_colors, foreground_color,
                 background_color, accent_color, isBwImg, height, width, image_format, request_id, landmarks=None, celebrities=None, ):
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
