import os
import yt_dlp
import json
import sys

# Add this at the top of the file
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads")

def find_ffmpeg(base_path):
    print(f"Searching for FFmpeg in: {base_path}")
    ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
    ffprobe_path = os.path.join(base_path, "ffprobe.exe")
    
    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        return ffmpeg_path, ffprobe_path
    return None, None

base_ffmpeg_path = os.getenv('FFMPEG_PATH', r"C:\ffmpeg-master-latest-win64-gpl\bin")
ffmpeg_path, ffprobe_path = find_ffmpeg(base_ffmpeg_path)

if ffmpeg_path and ffprobe_path:
    print(f"FFmpeg found at: {ffmpeg_path}")
    print(f"FFprobe found at: {ffprobe_path}")
    os.environ["PATH"] += os.pathsep + base_ffmpeg_path
else:
    print("FFmpeg executables not found. Please check the installation.")
    print(f"Contents of {base_ffmpeg_path}:")
    for file in os.listdir(base_ffmpeg_path):
        print(f"  File: {file}")

import re

def my_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'Unknown')
        # Remove ANSI escape codes
        percent = re.sub(r'\x1b\[[0-9;]*m', '', percent).strip()
        
        # Only print updates every 10%
        if int(float(percent.strip('%'))) % 10 == 0:
            progress = {
                'status': 'downloading',
                'filename': os.path.basename(d.get('filename', 'Unknown')),
                'percent': percent,
                'eta': d.get('_eta_str', 'Unknown')
            }
            # Send the progress update to the client
            event = f"data: {json.dumps(progress)}\n\n"
            sys.stdout.write(event)
            sys.stdout.flush()
    elif d['status'] == 'finished':
        progress = {
            'status': 'finished',
            'filename': os.path.basename(d.get('filename', 'Unknown'))
        }
        # Send the finished update to the client
        event = f"data: {json.dumps(progress)}\n\n"
        sys.stdout.write(event)
        sys.stdout.flush()

def download_content(url, output_path, format_type, quality='best'):
    ydl_opts = {
        'outtmpl': output_path,
        'ffmpeg_location': base_ffmpeg_path,
        'progress_hooks': [my_hook],
    }
    
    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # mp4
        if quality == '720p':
            format_spec = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif quality == '1080p':
            format_spec = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif quality == '4k':
            format_spec = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]/best'
        else:  # best
            format_spec = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        ydl_opts.update({
            'format': format_spec,
        })
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
    # Check and rename file if needed
    if format_type == 'mp3':
        base, ext = os.path.splitext(filename)
        # Fix the double extension issue
        if ext == '.mp3.mp3':
            new_filename = base + '.mp3'
            os.rename(filename, new_filename)
            filename = new_filename
        elif ext == '.mp3':  # Ensure it doesn't have an extra extension
            filename = filename  # No change needed

    # Verify the file exists
    if os.path.exists(filename):
        print(f"Found file: {filename}")
        return filename
    
    # Check possible variations
    for possible_ext in ['.mp3', '.mp3.mp3']:
        possible_file = base + possible_ext
        if os.path.exists(possible_file):
            print(f"Found file with variation: {possible_file}")
            return possible_file
    
    print("File not found.")
    return None