"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              video_processor.py                             ║
║                                                                              ║
║  Author: Vanessa Crosby                                                      ║
║  Date Created: August 23, 2025                                              ║
║  File Purpose: YouTube transcript extraction with OAuth authentication      ║
║  Date Modified: August 23, 2025 5:15 PM                                     ║
║  Mod Purpose: Added OAuth flow for YouTube Data API caption downloads       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import tempfile
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from pydub import AudioSegment
import streamlit as st
import re
import requests
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from audio_synchronizer import AudioSynchronizer

class VideoProcessor:

    def __init__(self):
        self.supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm']
        self.youtube_service = None
        self.oauth_creds = None
        self.audio_sync = AudioSynchronizer()

    def extract_video_id(self, youtube_url):
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)

        raise ValueError("Could not extract video ID from URL")

    def _setup_oauth_flow(self):
        oauth_json = os.environ.get('GOOGLE_OAUTH_CREDENTIALS_JSON')
        if not oauth_json:
            raise Exception("GOOGLE_OAUTH_CREDENTIALS_JSON not found in environment variables")

        oauth_config = json.loads(oauth_json)

        flow = Flow.from_client_config(
            oauth_config,
            scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

        return flow

    def get_oauth_url(self):
        try:
            flow = self._setup_oauth_flow()
            auth_url, _ = flow.authorization_url(prompt='consent')
            return auth_url, flow
        except Exception as e:
            raise Exception(f"Failed to setup OAuth: {str(e)}")

    def complete_oauth_flow(self, flow, auth_code):
        try:
            flow.fetch_token(code=auth_code)
            self.oauth_creds = flow.credentials

            self.youtube_service = build('youtube', 'v3', credentials=self.oauth_creds)
            return True
        except Exception as e:
            raise Exception(f"OAuth authentication failed: {str(e)}")

    def get_youtube_transcript_oauth(self, youtube_url):
        if not self.youtube_service:
            raise Exception("OAuth authentication required. Please authenticate first.")

        try:
            video_id = self.extract_video_id(youtube_url)

            captions_response = self.youtube_service.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()

            if not captions_response.get('items'):
                raise Exception("No captions found for this video")

            caption_id = None
            for caption in captions_response['items']:
                if caption['snippet']['language'] == 'en':
                    caption_id = caption['id']
                    break

            if not caption_id:
                caption_id = captions_response['items'][0]['id']

            caption_content = self.youtube_service.captions().download(
                id=caption_id,
                tfmt='srt'
            ).execute()

            if isinstance(caption_content, bytes):
                caption_content = caption_content.decode('utf-8')

            transcript_text = self._parse_srt_to_text(caption_content)
            return self._clean_transcript(transcript_text)

        except Exception as e:
            raise Exception(f"YouTube OAuth API failed: {str(e)}")

    def get_youtube_transcript_official_api(self, youtube_url):
        try:
            video_id = self.extract_video_id(youtube_url)
            api_key = os.environ.get('YOUTUBE_API_KEY')

            if not api_key:
                raise Exception("YOUTUBE_API_KEY not found in environment variables")

            captions_url = f"https://www.googleapis.com/youtube/v3/captions"
            params = {
                'part': 'snippet',
                'videoId': video_id,
                'key': api_key
            }

            response = requests.get(captions_url, params=params)
            response.raise_for_status()
            captions_data = response.json()

            if not captions_data.get('items'):
                raise Exception("No captions found for this video via YouTube Data API")

            caption_id = None
            for caption in captions_data['items']:
                if caption['snippet']['language'] == 'en':
                    caption_id = caption['id']
                    break

            if not caption_id:
                caption_id = captions_data['items'][0]['id']

            download_url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}"
            download_params = {
                'key': api_key,
                'tfmt': 'srt'
            }

            caption_response = requests.get(download_url, params=download_params)
            caption_response.raise_for_status()

            srt_content = caption_response.text
            transcript_text = self._parse_srt_to_text(srt_content)

            return self._clean_transcript(transcript_text)

        except Exception as e:
            raise Exception(f"YouTube Data API failed: {str(e)}")

    def _parse_srt_to_text(self, srt_content):
        lines = srt_content.strip().split('\n')
        text_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.isdigit() and '-->' not in line:
                text_lines.append(line)

        return ' '.join(text_lines)

    def get_youtube_transcript(self, youtube_url):
        try:
            video_id = self.extract_video_id(youtube_url)
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)

            try:
                english_transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            except:
                available_transcripts = list(transcript_list)
                if not available_transcripts:
                    raise Exception("No transcripts available for this video")
                english_transcript = available_transcripts[0]

            fetched_data = english_transcript.fetch()
            full_transcript = ' '.join([snippet.text for snippet in fetched_data.snippets])
            full_transcript = self._clean_transcript(full_transcript)

            return full_transcript

        except Exception as e:
            return self._fallback_transcript_extraction(youtube_url)

    def _clean_transcript(self, transcript):
        transcript = re.sub(r'\s+', ' ', transcript)
        transcript = re.sub(r'\[.*?\]', '', transcript)
        transcript = re.sub(r'\(.*?\)', '', transcript)
        transcript = transcript.replace(' uh ', ' ')
        transcript = transcript.replace(' um ', ' ')
        transcript = transcript.replace(' er ', ' ')
        return transcript.strip()

    def _fallback_transcript_extraction(self, youtube_url):
        try:
            video_id = self.extract_video_id(youtube_url)

            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)

                subtitles = info_dict.get('subtitles') if info_dict.get('subtitles') is not None else {}
                auto_captions = info_dict.get('automatic_captions') if info_dict.get('automatic_captions') is not None else {}

                for lang in ['en', 'en-US', 'en-GB']:
                    if lang in subtitles:
                        return self._extract_text_from_subtitles(subtitles[lang])
                    elif lang in auto_captions:
                        return self._extract_text_from_subtitles(auto_captions[lang])

                all_subs = {**subtitles, **auto_captions}
                if all_subs:
                    first_lang = list(all_subs.keys())[0]
                    return self._extract_text_from_subtitles(all_subs[first_lang])

                raise Exception("No subtitles found for this video")

        except Exception as e:
            raise Exception(f"Could not extract transcript: {str(e)}")

    def _extract_text_from_subtitles(self, subtitle_formats):
        try:
            vtt_format = next((fmt for fmt in subtitle_formats if fmt.get('ext') == 'vtt'), None)
            if vtt_format:
                return "Transcript extraction from subtitles not fully implemented"

            return "Could not extract text from available subtitle formats"

        except Exception:
            return "Error processing subtitle formats"

    def download_youtube_video(self, url, output_dir):
        transcript = self.get_youtube_transcript(url)
        transcript_path = os.path.join(output_dir, "transcript.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        return "TRANSCRIPT_ONLY"

    def _get_duration(self, file_path):
        if file_path == "TRANSCRIPT_ONLY":
            return 0

        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0

    def replace_audio(self, video_path, new_audio_path, output_dir, sync_method="smart", progress_callback=None):
        try:
            if video_path == "TRANSCRIPT_ONLY":
                output_path = os.path.join(output_dir, "output_audio.mp3")
                import shutil
                shutil.copy2(new_audio_path, output_path)
                return output_path

            video_duration = self._get_duration(video_path)
            audio_duration = self._get_duration(new_audio_path)

            output_path = os.path.join(output_dir, "output_video.mp4")
            
            print(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s")

            # Try smart sync first (default method)
            if sync_method == "smart":
                try:
                    print("Using smart audio synchronization")
                    if progress_callback:
                        progress_callback(10)
                    
                    # Use smart sync to create perfectly timed audio
                    def smart_progress(p):
                        if progress_callback:
                            progress_callback(10 + int(p * 0.7))  # 10-80% for smart sync
                    
                    synchronized_audio = self.audio_sync.smart_sync(
                        video_path, new_audio_path, output_dir, smart_progress
                    )
                    
                    if progress_callback:
                        progress_callback(80)
                    
                    # Now combine with video using the synchronized audio
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-i', synchronized_audio,
                        '-c:v', 'copy',
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        '-shortest',
                        output_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        if progress_callback:
                            progress_callback(100)
                        final_duration = self._get_duration(output_path)
                        print(f"Smart sync successful! Final duration: {final_duration:.2f}s")
                        return output_path
                    else:
                        print(f"Video combination failed, falling back to stretch method: {result.stderr}")
                        
                except Exception as e:
                    print(f"Smart sync failed, falling back to stretch method: {str(e)}")
                
                # Fallback to stretch method
                sync_method = "stretch"
                print("Falling back to stretch method")

            if sync_method == "stretch" and video_duration > 0 and audio_duration > 0:
                # Method 1: Stretch/compress audio to match video duration
                tempo_ratio = audio_duration / video_duration
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', new_audio_path,
                    '-c:v', 'copy',
                    '-filter:a', f'atempo={tempo_ratio:.3f}',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    output_path
                ]
                print(f"Using audio stretching with tempo ratio: {tempo_ratio:.3f}")
                
            elif sync_method == "loop" and video_duration > audio_duration:
                # Method 2: Loop audio to match video duration
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-stream_loop', '-1',
                    '-i', new_audio_path,
                    '-c:v', 'copy',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    output_path
                ]
                print("Using audio looping to match video duration")
                
            elif sync_method == "fade":
                # Method 3: Fade audio in/out to match duration
                if audio_duration < video_duration:
                    # Pad with silence and fade
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-i', new_audio_path,
                        '-c:v', 'copy',
                        '-filter:a', f'apad=whole_dur={video_duration}',
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        '-t', str(video_duration),
                        output_path
                    ]
                else:
                    # Fade out at video end
                    fade_start = max(0, video_duration - 2)  # Start fade 2 seconds before end
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-i', new_audio_path,
                        '-c:v', 'copy',
                        '-filter:a', f'afade=t=out:st={fade_start}:d=2',
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        '-t', str(video_duration),
                        output_path
                    ]
                print(f"Using audio fade with video duration: {video_duration:.2f}s")
            else:
                # Default: Use shortest duration (original method)
                cmd = [
                    'ffmpeg', '-y',
                    '-i', video_path,
                    '-i', new_audio_path,
                    '-c:v', 'copy',
                    '-map', '0:v:0',
                    '-map', '1:a:0',
                    '-shortest',
                    output_path
                ]
                print("Using shortest duration method")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            final_duration = self._get_duration(output_path)
            print(f"Final video duration: {final_duration:.2f}s")

            return output_path

        except Exception as e:
            raise Exception(f"Failed to replace audio in video: {str(e)}")

    def get_video_info(self, video_path):
        try:
            if video_path == "TRANSCRIPT_ONLY":
                return {
                    'duration': 0,
                    'fps': 0,
                    'size': (0, 0),
                    'has_audio': False,
                    'transcript_only': True
                }

            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"FFprobe failed: {result.stderr}")

            import json
            probe_data = json.loads(result.stdout)

            video_stream = next((stream for stream in probe_data['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe_data['streams'] if stream['codec_type'] == 'audio'), None)

            info = {
                'duration': float(probe_data['format']['duration']) if 'duration' in probe_data['format'] else 0,
                'fps': eval(video_stream['r_frame_rate']) if video_stream and 'r_frame_rate' in video_stream else 0,
                'size': (int(video_stream['width']), int(video_stream['height'])) if video_stream else (0, 0),
                'has_audio': audio_stream is not None,
                'transcript_only': False
            }

            return info

        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")