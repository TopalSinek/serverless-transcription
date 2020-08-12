# This function is triggered by an S3 event when an object is created. It
# starts a extracting the audio from the video file. This will have a lot of limitation on size and video type
# A better solution is avaible with AWS ElasticTranscoder but is not needed for MVP

import boto3
import os
import re
import urllib.parse
import uuid
import subprocess
# import moviepy.editor as mp

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')
efsPath = os.environ['EFS_FILEPATH']
audioOutputBucket = os.environ['AUDIO_OUTPUT_BUCKET']

s3_host = f"s3-{os.environ['AWS_REGION']}.amazonaws.com"


def get_media_format(path):
    if re.search('.mp4$', path) is not None:
        return 'mp4'
    elif re.search('.3gp$', path) is not None:
        return '3gp'
    elif re.search('.wmv$', path) is not None:
        return 'wmv'
    elif re.search('.wma$', path) is not None:
        return 'wmv'
    elif re.search('.ogg$', path) is not None:
        return 'ogg'
    else:
        return 'mp3'


def get_s3_metadata(bucket, key):
    return s3.head_object(Bucket=bucket, Key=key)['Metadata']


def lambda_handler(event, context):

    # Generate a unique name for the job
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    _object_key = event['Records'][0]['s3']['object']['key']
    object_key = urllib.parse.unquote_plus(_object_key)
    uniqueId= str(uuid.uuid4())
    filenameWithoutExt = os.path.splitext(object_key)[0]
    soundFileName = f"{uniqueId}-sound-{filenameWithoutExt}"
    videoFileName = f"{uniqueId}-video-{object_key}"

    print(f"Starting transcode job: {soundFileName}")
    print(f"Object: {bucket_name}/{object_key}")

    media_metadata = get_s3_metadata(bucket_name, object_key)
    print("Media_metadata:", media_metadata)
    channel_identification = media_metadata.get('channelidentification', 'On')
    # Language list: en-US | es-US | en-AU | fr-CA | en-GB | de-DE | pt-BR | fr-FR | it-IT | ko-KR | es-ES | en-IN | hi-IN | ar-SA | ru-RU | zh-CN | nl-NL | id-ID | ta-IN | fa-IR | en-IE | en-AB | en-WL | pt-PT | te-IN | tr-TR | de-CH | he-IL | ms-MY | ja-JP | ar-AE
    # See https://docs.aws.amazon.com/transcribe/latest/dg/API_StartTranscriptionJob.html for the most up-to-date list of languages available.
    language_code = media_metadata.get('languagecode', 'en-US')
    max_speaker_labels = int(media_metadata.get('maxspeakerlabels', '1'))


    s3.download_file(Bucket=bucket_name, Key=object_key, Filename=f"{efsPath}/{videoFileName}")

    # clip = mp.VideoFileClip(f"{efsPath}/{videoFileName}")
    # clip.audio.write_audiofile(f"{efsPath}/{soundFileName}.mp3")
    subprocess.call(['ffmpeg', '-i', f"{efsPath}/{videoFileName}", '-vn', '-acodec', 'copy', f"{efsPath}/{soundFileName}.mp3"])
    with open(f"{efsPath}/{soundFileName}.mp3", 'rb') as f:
        data = f.read()
        s3.Object(audioOutputBucket, f"{soundFileName}.mp3").put(Body=data, Metadata={'languagecode': language_code,
                                                                                      'channelidentification': channel_identification,
                                                                                      'maxspeakerlabels': max_speaker_labels})
