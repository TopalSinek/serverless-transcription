# This function is triggered by an S3 event when an object is created. It
# starts a transcription job with the media file, and sends an email notifying
# the user that the job has started.

import boto3
import uuid
import os
import re
import urllib.parse
from datetime import datetime

s3 = boto3.client('s3')
ses = boto3.client('ses')
transcribe = boto3.client('transcribe')

s3_host = f"s3-{os.environ['AWS_REGION']}.amazonaws.com"


def get_media_format(path):
    if re.search('.mp3$', path) is not None:
        return 'mp3'
    elif re.search('.mp4$', path) is not None:
        return 'mp4'
    elif re.search('.m4a$', path) is not None:
        return 'mp4'
    elif re.search('.wav$', path) is not None:
        return 'wav'
    elif re.search('.flac$', path) is not None:
        return 'flac'
    else:
        return 'mp3'


def get_s3_metadata(bucket, key):
    return s3.head_object(Bucket=bucket, Key=key)['Metadata']


def lambda_handler(event, context):

    # Generate a unique name for the job
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    _object_key = event['Records'][0]['s3']['object']['key']
    object_key = urllib.parse.unquote_plus(_object_key)
    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
    transcription_job_name = f"{object_key}-{dt_string}"

    print(f"Starting transcription job: {transcription_job_name}")
    print(f"Object: {bucket_name}/{object_key}")

    media_metadata = get_s3_metadata(bucket_name, object_key)
    print("Media_metadata:", media_metadata)
    channel_identification = media_metadata.get('channelidentification', 'On')
    # Language list: en-US | es-US | en-AU | fr-CA | en-GB | de-DE | pt-BR | fr-FR | it-IT | ko-KR | es-ES | en-IN | hi-IN | ar-SA | ru-RU | zh-CN | nl-NL | id-ID | ta-IN | fa-IR | en-IE | en-AB | en-WL | pt-PT | te-IN | tr-TR | de-CH | he-IL | ms-MY | ja-JP | ar-AE
    # See https://docs.aws.amazon.com/transcribe/latest/dg/API_StartTranscriptionJob.html for the most up-to-date list of languages available.
    language_code = media_metadata.get('languagecode', 'en-US')
    max_speaker_labels = int(media_metadata.get('maxspeakerlabels', '1'))

    transcription_job_settings = {
        'ChannelIdentification': channel_identification == 'On',
        'ShowSpeakerLabels': channel_identification != 'On'
    }

    if channel_identification != 'On':
        transcription_job_settings['MaxSpeakerLabels'] = max_speaker_labels

    transcribe.start_transcription_job(
        TranscriptionJobName=f"{transcription_job_name}",
        LanguageCode=language_code,
        MediaFormat=get_media_format(object_key),
        Media={
            'MediaFileUri': f"https://{s3_host}/{bucket_name}/{object_key}"
        },
        Settings=transcription_job_settings,
        OutputBucketName=os.environ['TRANSCRIPTIONS_OUTPUT_BUCKET'],
    )
