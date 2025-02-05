import os
import tempfile
import subprocess
import re
import time
import json
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import *

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
mongo_collection = mongo_db[MONGO_COLLECTION_NAME]

mongo_collection.create_index("user_id", unique=True)

USERS_FILE = 'users.json'

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

encoding_settings = {
    "144p": {"scale": "256:144", "bitrate": "300k", "crf": 30},
    "360p": {"scale": "640:360", "bitrate": "800k", "crf": 28},
    "480p": {"scale": "854:480", "bitrate": "1200k", "crf": 23},
    "720p": {"scale": "1280:720", "bitrate": "2500k", "crf": 20},
    "1080p": {"scale": "1920:1080", "bitrate": "5000k", "crf": 18},
    "2k": {"scale": "2560:1440", "bitrate": "8000k", "crf": 16},
}

user_settings = {}

channel_name = "Encoded By @GenAnimeOfc"
ownerz = "DARKXSIDE78"

ffmpeg_time_regex = re.compile(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})')

PROGRESS_BAR = """<b>
╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣
┣⪼ 🗃️ Sɪᴢᴇ: {1} / {2}
┣⪼ ⏳️ Dᴏɴᴇ : {0}%
┣⪼ 🚀 Sᴩᴇᴇᴅ: {3}/s
┣⪼ ⏰️ Eᴛᴀ: {4}
╰━━━━━━━━━━━━━━━➣ </b>"""

def format_size(bytes):
    """Convert bytes to a human-readable format."""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 ** 2:
        return f"{bytes / 1024:.2f} KB"
    elif bytes < 1024 ** 3:
        return f"{bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{bytes / (1024 ** 3):.2f} GB"

def format_speed(bytes_per_sec):
    """Convert bytes per second to a human-readable format."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.2f} B"
    elif bytes_per_sec < 1024**2:
        return f"{bytes_per_sec / 1024:.2f} KB"
    elif bytes_per_sec < 1024**3:
        return f"{bytes_per_sec / (1024**2):.2f} MB"
    else:
        return f"{bytes_per_sec / (1024**3):.2f} GB"

def format_eta(seconds):
    """Format seconds to HH:MM:SS."""
    return time.strftime("%H:%M:%S", time.gmtime(seconds))

def time_to_seconds(time_str):
    """Convert HH:MM:SS.ss to seconds."""
    try:
        h, m, s = map(float, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except:
        return 0

def get_video_duration(file):
    """Extract total duration of the video using FFprobe."""
    command = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file}"'
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10)
        duration = float(result.stdout.strip())
        return duration
    except subprocess.TimeoutExpired:
        print(f"Timeout expired while processing {file}.")
        return 0
    except ValueError:
        print(f"Could not parse duration for {file}.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

class Progress:
    """Class to handle progress updates."""
    
    def __init__(self, message: Message):
        self.message = message
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_bytes = 0

    def update(self, current: int, total: int):
        """Update the progress bar."""
        now = time.time()
        elapsed = now - self.start_time
        delta_time = now - self.last_update_time
        delta_bytes = current - self.last_bytes

        # Update the last values
        self.last_update_time = now
        self.last_bytes = current

        # Calculate download speed, ETA, and percentage
        speed = delta_bytes / delta_time if delta_time > 0 else 0
        eta = (total - current) / speed if speed > 0 else float("inf")
        percentage = (current / total) * 100 if total > 0 else 0

        # Format the output strings
        formatted_current = format_size(current)
        formatted_total = format_size(total)
        speed_str = format_speed(speed)
        eta_str = format_eta(eta)

        # Construct the progress message
        progress_text = PROGRESS_BAR.format(
            round(percentage, 2),
            formatted_current,
            formatted_total,
            speed_str,
            eta_str
        )
        try:
            self.message.edit_text(progress_text)
        except Exception as e:
            print(f"Failed to update progress message: {e}")

class EncodingProgress:
    """Class to handle encoding progress updates."""
    def __init__(self, message: Message, total_duration: float, total_size: int):
        self.message = message
        self.total_duration = total_duration
        self.total_size = total_size
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_bytes = 0
        self.fps = 0

    def update(self, current_time_str: str, current_bytes: int):
        """Update the encoding progress bar."""
        current_seconds = time_to_seconds(current_time_str)
        elapsed = time.time() - self.start_time

        if self.total_duration > 0 and current_seconds > 0:
            progress_percentage = (current_seconds / self.total_duration) * 100
            speed = (current_bytes - self.last_bytes) / (time.time() - self.last_update_time) if (time.time() - self.last_update_time) > 0 else 0
            eta = (self.total_duration - current_seconds) / (current_seconds / elapsed) if (current_seconds / elapsed) > 0 else float("inf")
            self.fps = (current_seconds / elapsed) if elapsed > 0 else 0
        else:
            progress_percentage = 0
            speed = 0
            eta = 0

        self.last_update_time = time.time()
        self.last_bytes = current_bytes

        formatted_current = format_size(current_bytes)
        formatted_total = format_size(self.total_size)
        speed_str = format_speed(speed)
        eta_str = format_eta(eta)

        progress_text = f"""<b>
╭━━━━❰ᴇɴᴄᴏᴅɪɴɢ ᴘʀᴏɢʀᴇss❱━➣
┣⪼ 🗃️ Sɪᴢᴇ: {formatted_current} / {formatted_total}
┣⪼ ⏳️ Dᴏɴᴇ : {round(progress_percentage, 2)}%
┣⪼ 🚀 Sᴩᴇᴇᴅ: {speed_str}/s
┣⪼ ⏰️ Eᴛᴀ: {eta_str}
┣⪼ 🎞️ FPS: {round(self.fps, 2)}
╰━━━━━━━━━━━━━━━➣ </b>"""

        try:
            self.message.edit_text(progress_text)
        except Exception as e:
            print(f"Failed to update encoding progress message: {e}")

local_directory = "user_data"
if not os.path.exists(local_directory):
    os.makedirs(local_directory)

def store_user_data(user):
    """Store user data in MongoDB and local JSON file."""
    user_data = {
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}" if user.last_name else user.first_name,
        "phone_number": user.phone_number if user.phone_number else "N/A",
    }

    try:
        mongo_collection.update_one({"user_id": user.id}, {"$set": user_data}, upsert=True)
    except Exception as e:
        print(f"MongoDB Error: {e}")

    file_path = os.path.join(local_directory, f"{user.id}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(user_data, f, indent=4)
    except Exception as e:
        print(f"File Storage Error: {e}")


@app.on_message(filters.command("start"))
def start(client, message: Message):
    """Handle the /start command."""
    user = message.from_user
    store_user_data(user)
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Compress Audio 🎧", callback_data="compress_audio"),
         InlineKeyboardButton("Compress Video 🎥", callback_data="compress_video")],
        [InlineKeyboardButton("Configure Settings ⚙️", callback_data="config")]
    ])
    message.reply_text("Choose what you want to compress:", reply_markup=markup)

@app.on_callback_query()
def callback(client, callback_query: CallbackQuery):
    """Handle callback queries from inline buttons."""
    if callback_query.data == "compress_audio":
        callback_query.message.reply_text("Send me an audio file.")
    elif callback_query.data == "compress_video":
        callback_query.message.reply_text("Send me a video file.")
    elif callback_query.data == "config":
        user_id = callback_query.from_user.id
        user_setting = user_settings.get(user_id, {})
        config_text = "\n".join([
            f"{resolution}: Scale={settings['scale']}, Bitrate={settings['bitrate']}, CRF={settings['crf']}" 
            for resolution, settings in encoding_settings.items()
        ])
        callback_query.message.reply_text(
            f"Current encoding settings:\n{config_text}\n\nUse /set_resolution <resolution> to change settings."
        )

@app.on_message(filters.voice | filters.audio)
def handle_audio(client, message: Message):
    """Handle incoming audio files."""
    file_id = message.voice.file_id if message.chat.type == "voice" else message.audio.file_id
    download_msg = message.reply_text("Downloading audio...")
    progress = Progress(download_msg)

    try:
        file_path = client.download_media(file_id, progress=download_progress, progress_args=(progress,))
    except Exception as e:
        download_msg.edit_text(f"Failed to download audio: {e}")
        return

    download_msg.edit_text("Encoding audio...")
    try:
        audio = AudioSegment.from_file(file_path).set_channels(AUDIO_CHANNELS).set_frame_rate(AUDIO_SAMPLE_RATE)
    except Exception as e:
        download_msg.edit_text(f"Failed to process audio: {e}")
        os.remove(file_path)
        return

    try:
        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX_AUDIO, delete=False) as temp_file:
            temp_filename = temp_file.name
            audio.export(temp_filename, format=AUDIO_FORMAT, bitrate=AUDIO_BITRATE)
    except Exception as e:
        download_msg.edit_text(f"Failed to encode audio: {e}")
        os.remove(file_path)
        return

    try:
        upload_msg = message.reply_text("Uploading compressed audio...")
        upload_progress_instance = Progress(upload_msg)
        client.send_document(
            chat_id=message.chat.id,
            document=temp_filename,
            caption="Here is your compressed audio.",
            progress=upload_progress,
            progress_args=(upload_progress_instance,)
        )
    except Exception as e:
        upload_msg.edit_text(f"Failed to upload audio: {e}")
    finally:
        download_msg.delete()
        upload_msg.delete()
        os.remove(file_path)
        os.remove(temp_filename)

@app.on_message(filters.video | filters.animation | filters.document)
def handle_media(client, message: Message):
    """Handle incoming video files, including MKV documents."""
    is_document = False
    mime_type = ""
    file_extension = ""

    if message.document:
        if message.document.mime_type.startswith("video/"):
            is_document = True
            mime_type = message.document.mime_type
            file_extension = os.path.splitext(message.document.file_name)[1].lower()
    elif message.video:
        mime_type = message.video.mime_type
        file_extension = os.path.splitext(message.video.file_name)[1].lower() if message.video.file_name else '.mp4'
    elif message.animation:
        mime_type = message.animation.mime_type
        file_extension = os.path.splitext(message.animation.file_name)[1].lower() if message.animation.file_name else '.mp4'

    if not (is_document or message.video or message.animation):
        return

    download_msg = message.reply_text("Downloading video...")
    progress = Progress(download_msg)
    try:
        if is_document:
            file_path = client.download_media(message.document.file_id, progress=download_progress, progress_args=(progress,))
        elif message.video:
            file_path = client.download_media(message.video.file_id, progress=download_progress, progress_args=(progress,))
        elif message.animation:
            file_path = client.download_media(message.animation.file_id, progress=download_progress, progress_args=(progress,))
    except Exception as e:
        download_msg.edit_text(f"Failed to download video: {e}")
        return

    # Determine output suffix based on input format
    if is_document:
        if file_extension in ['.mkv', '.webm', '.avi', '.flv', '.mov']:
            output_suffix = file_extension
        else:
            output_suffix = '.mp4'  # Default to mp4 for unknown extensions
    else:
        if mime_type == "video/x-matroska":
            output_suffix = '.mkv'
        else:
            output_suffix = '.mp4'

    with tempfile.NamedTemporaryFile(suffix=output_suffix, delete=False) as temp_file:
        temp_filename = temp_file.name

    user_id = message.from_user.id
    user_setting = user_settings.get(user_id, {})
    resolution = user_setting.get("resolution", "720p")
    encoding_setting = encoding_settings.get(resolution, encoding_settings["720p"])

    total_duration = get_video_duration(file_path)

    if total_duration == 0:
        encoding_msg = message.reply_text("Encoding video...")
        ffmpeg_command = (
            f'ffmpeg -y -i "{file_path}" '
            f'-filter_complex "scale={encoding_setting["scale"]},unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=2" '
            f'-c:v libx264'  # Using libx265 video codec with custom bitrate
            f'-crf 27 -preset veryfast '  # CRF and preset for quality and speed
            f'-threads 0 '  # Allow ffmpeg to use all available CPU threads
            f'-c:a aac -b:a 35k '  # Using AAC audio codec with 128k bitrate
            f'-ac 2'  # Stereo audio with 44.1kHz sample rate
            f'-map 0 '  # Map all streams
            f'-metadata title="GenAnimeOfc [t.me/GenAnimeOfc]" '  # Adding video title metadata
            f'-metadata artist="DAARKXSIDE78" '  # Adding artist metadata
            f'-metadata author="DARKXSIDE78" '  # Adding author metadata
            f'-metadata:s:s title="[GenAnimeOfc]" '  # Subtitle track title metadata
            f'-metadata:s:v title="[GenAnimeOfc]" '
            f'-metadata:s:a title="[GenAnimeOfc]" '
            f'"{temp_filename}"'  # Output file path
        )


        try:
            subprocess.run(ffmpeg_command, shell=True, check=True)
            encoding_msg.edit_text("Encoding completed. Uploading video...")
        except subprocess.CalledProcessError as e:
            encoding_msg.edit_text(f"Failed to encode video: {e}")
            os.remove(file_path)
            os.remove(temp_filename)
            return

        try:
            upload_msg = message.reply_text("Uploading video...")
            upload_progress_instance = Progress(upload_msg)
            client.send_document(
                chat_id=message.chat.id,
                document=temp_filename,
                caption="Here is your compressed video.",
                progress=upload_progress,
                progress_args=(upload_progress_instance,)
            )
        except Exception as e:
            upload_msg.edit_text(f"Failed to upload video: {e}")
        finally:
            download_msg.delete()
            encoding_msg.delete()
            upload_msg.delete()
            os.remove(file_path)
            os.remove(temp_filename)
        return

    total_size = os.path.getsize(file_path)

    encoding_msg = message.reply_text("Encoding video...")
    encoding_progress = EncodingProgress(encoding_msg, total_duration, total_size)

    ffmpeg_command = (
        f'ffmpeg -y -i "{file_path}" '
        f'-filter_complex "scale={encoding_setting["scale"]}" '
        f'-c:v libx265 -b:v {encoding_setting["bitrate"]} '
        f'-crf {encoding_setting["crf"]} -preset fast '
        f'-threads 0 '
        f'-c:a aac -b:a 128k '
        f'-ac 2 -ar 44100 '
        f'-map 0 '
        f'-map_metadata -1 "{temp_filename}"'
    )

    process = subprocess.Popen(ffmpeg_command, shell=True, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')

    while True:
        line = process.stderr.readline()
        if not line:
            break
        if "time=" in line:
            current_time_match = ffmpeg_time_regex.search(line)
            if current_time_match:
                current_time_str = current_time_match.group(1)
                encoding_progress.update(current_time_str, total_size)

    process.wait()

    if process.returncode != 0:
        encoding_msg.edit_text("Failed to encode video.")
        os.remove(file_path)
        os.remove(temp_filename)
        return

    encoding_msg.edit_text("Encoding completed. Uploading video...")

    try:
        upload_msg = message.reply_text("Uploading video...")
        upload_progress_instance = Progress(upload_msg)
        client.send_document(
            chat_id=message.chat.id,
            document=temp_filename,
            caption="Here is your compressed video.",
            progress=upload_progress,
            progress_args=(upload_progress_instance,)
        )
    except Exception as e:
        upload_msg.edit_text(f"Failed to upload video: {e}")
    finally:
        download_msg.delete()
        encoding_msg.delete()
        upload_msg.delete()
        os.remove(file_path)
        os.remove(temp_filename)

def download_progress(current, total, progress: Progress):
    """Progress callback for downloading."""
    progress.update(current, total)

def upload_progress(current, total, progress: Progress):
    """Progress callback for uploading."""
    progress.update(current, total)

@app.on_message(filters.command("owner"))
def set_owner(client, message: Message):
    """Handle the /owner command."""
    args = message.command[1:]
    if len(args) == 0:
        message.reply_text("Usage: /owner <name>")
        return

    owner_name = " ".join(args)
    user_id = message.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["ownerz"] = owner_name

    try:
        mongo_collection.update_one(
            {"user_id": user_id},
            {"$set": {"ownerz": owner_name}}
        )
    except Exception as e:
        print(f"MongoDB Update Error: {e}")

    try:
        with open(os.path.join(local_directory, f"{user_id}.json"), 'r+') as f:
            data = json.load(f)
            data['ownerz'] = owner_name
            f.seek(0)
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"File Storage Update Error: {e}")

    message.reply_text(f"Artist set to: {owner_name}")

@app.on_message(filters.command("set_resolution"))
def set_resolution(client, message: Message):
    """Handle the /set_resolution command."""
    args = message.command[1:]
    if len(args) != 1:
        message.reply_text("Usage: /set_resolution <resolution>")
        return

    resolution = args[0].lower()
    if resolution in encoding_settings:
        user_id = message.from_user.id
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]["resolution"] = resolution

        try:
            mongo_collection.update_one(
                {"user_id": user_id},
                {"$set": {"resolution": resolution}}
            )
        except Exception as e:
            print(f"MongoDB Update Error: {e}")

        try:
            with open(os.path.join(local_directory, f"{user_id}.json"), 'r+') as f:
                data = json.load(f)
                data['resolution'] = resolution
                f.seek(0)
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"File Storage Update Error: {e}")

        message.reply_text(f"Resolution set to {resolution}.")
    else:
        message.reply_text("Invalid resolution. Available options are: 144p, 360p, 480p, 720p, 1080p, 2k.")

@app.on_message(filters.command("metadata"))
def set_metadata(client, message: Message):
    """Handle the /metadata command."""
    args = message.command[1:]
    if len(args) == 0:
        message.reply_text("Usage: /metadata <text you want to put>")
        return

    metadata_text = " ".join(args)
    user_id = message.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["channel_name"] = metadata_text

    try:
        mongo_collection.update_one(
            {"user_id": user_id},
            {"$set": {"channel_name": metadata_text}}
        )
    except Exception as e:
        print(f"MongoDB Update Error: {e}")

    try:
        with open(os.path.join(local_directory, f"{user_id}.json"), 'r+') as f:
            data = json.load(f)
            data['channel_name'] = metadata_text
            f.seek(0)
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"File Storage Update Error: {e}")

    message.reply_text(f"Channel name for metadata set to: {metadata_text}")

@app.on_message(filters.command("config"))
def config_command(client, message: Message):
    """Handle the /config command."""
    user_id = message.from_user.id
    user_setting = user_settings.get(user_id, {})
    config_text = "\n".join([
        f"{resolution}: Scale={settings['scale']}, Bitrate={settings['bitrate']}, CRF={settings['crf']}" 
        for resolution, settings in encoding_settings.items()
    ])
    message.reply_text(
        f"Current encoding settings:\n{config_text}\n\nUse /set_resolution <resolution> to change settings."
    )

print("Starting Bot...")
print("Join My Channel @GenAnimeOfc")
print("CopyRight By DARKXSIDE78\nDev: DARKXSIDE78\nDev: にちん\nDARK: The Night Is Ours!\nIn the Depths of DARK, We Find Strength!")
print("Bot Started...")
app.run()
