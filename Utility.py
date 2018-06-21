import os
from enum import Enum
from Models import *

#
# Constants
#


#
# Enums
#
class GrabRateType(Enum):
    BY_FRAME = 0
    BY_SECOND = 1


class UploadType(Enum):
    LOCAL = 0
    REMOTE = 1


class Messages(Enum):
    INVALID_START_END_TIME = 'Please make sure start and end time is specified correctly. They should both be integer' \
                             ' values within the time range of the video (in seconds). '
    INVALID_GRAB_RATE = 'Please make sure grab rate is specified correctly. It should be a non-negative integer'
    FILE_NOT_FOUND = 'File is not found. Please make sure the file name and path is correct.'
    CONTAINER_NOT_FOUND = 'Container is not found. Please make sure the name is correct.'
    BLOB_NOT_FOUND = 'Blob is not found. Please make sure the name is correct.'


class Constants(Enum):
    CS_SUBSCRIPTION_HEADER = 'Ocp-Apim-Subscription-Key'


#
# Utility methods
#
def ms_to_std_time(time_in_ms):
    time_in_s = int(time_in_ms / 1000)
    ms_component = get_ms_component(time_in_ms)
    std_time_in_s = time_in_s % 60
    std_time_in_s_str = str(std_time_in_s) if std_time_in_s >= 10 else '0' + str(std_time_in_s)
    std_time_in_min = int((time_in_s - std_time_in_s) % 3600 / 60)
    std_time_in_min_str = str(std_time_in_min) if std_time_in_min >= 10 else '0' + str(std_time_in_min)
    std_time_in_hr = int((time_in_s - std_time_in_min * 60 - std_time_in_s) / 3600)
    std_time_in_hr_str = str(std_time_in_hr) if std_time_in_hr >= 10 else '0' + str(std_time_in_hr)
    std_time = std_time_in_hr_str + ':' + std_time_in_min_str + ':' + std_time_in_s_str + '.' + ms_component
    return std_time


def std_time_to_s(std_time):
    times = std_time.split(':')
    assert len(times) == 3
    return times[0] * 3600 + times[1] * 60 + times[2]


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


#
# Exceptions
#
class InvalidInputException(Exception):
    def __init__(self, arg):
        self.arg = arg
