import os
import time
import subprocess
import queue  # Import the queue module
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Running', 200

@app.route('/health')
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

app = Client("advancedVideoEncoderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "./downloads/"
ENCODING_FORMATS = {"h265": "libx265", "h264": "libx264"}
quality = "720p"  # Default quality setting
encoding_type = "libx264"  # Default encoding type
artist = "DARKXSIDE78"  # Default artist
author = "DARKXSIDE78"  # Default author
video_title = "GenAnimeOfc [t.me/GenAnimeOfc]"  # Default video title
subtitle_title = "[GenAnimeOfc]"  # Default subtitle track name

# Quality Resolutions
QUALITY_RESOLUTIONS = {
    "144p": "144",
    "360p": "360",
    "480p": "480",
    "720p": "720",
    "1080p": "1080",
    "2k": "1440"
}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

encoding_queue = queue.Queue()  # Initialize the encoding queue

def encode_video(input_file, output_file, encoding_type="libx265", resolution="720", video_title="Video", artist="Artist", author="Author", subtitle_title="Subtitle"):
    ffmpeg_cmd = [
        "ffmpeg", "-i", input_file, "-c:v", encoding_type, "-preset", "veryfast",
        "-crf", "27",  # Lower CRF for better quality (default is 23, you can adjust it)
        "-aq-mode", "2", "-tune", "film",  # Film tuning for anime to enhance quality
        "-g", "30",  # Adjust GOP size for better smoothness
        "-vsync", "2",  # Ensures smoother playback, especially for high FPS content
        "-c:a", "aac", "-b:a", "35k",  # Audio bitrate increased for better quality
        "-c:s", "copy",  # Copy subtitles
        "-vf", f"scale=-2:{resolution},unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=2",  # Sharpness filter added
        "-map", "0", "-ac", "2",  # Audio channels set to stereo
        "-metadata", f"artist={artist}",
        "-metadata:s:v", "title='[GenAnimeOfc]'",
        "-metadata:s:s", "title='[GenAnimeOfc]'",
        "-metadata:s:a", "title='[GenAnimeOfc]'",
        "-metadata", "title='GenAnimeOfc [t.me/GenAnimeOfc]'",
        "-metadata", "author='DARKXSIDE78'",  # Added metadata for author and title
        output_file,
    ]
    subprocess.run(ffmpeg_cmd)
    
async def process_queue():
    while not encoding_queue.empty():
        video = encoding_queue.get()
        input_file = video["input_file"]
        output_file = video["output_file"]
        await video["message"].reply(f"Starting encoding for {input_file}...")
        
        encode_video(input_file, output_file, encoding_type, quality, video_title, artist, author, subtitle_title)
        
        await video["message"].reply(f"Encoding completed! The encoded video is available at {output_file}")
        encoding_queue.task_done()

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("Bᴀᴋᴋᴀᴀ!!! 😜\nI ᴀᴍ ᴀ ᴠɪᴅᴇᴏ ᴇɴᴄᴏᴅᴇʀ ʙᴏᴛ ᴄʀᴇᴀᴛᴇᴅ ʙʏ @DARKXSIDE78 ᴛᴏ ᴇɴᴄᴏᴅᴇ ᴠɪᴅᴇᴏs ᴀɴᴅ ᴄᴏᴍᴘʀᴇss ᴛʜᴇᴍ ɪɴᴛᴏ sᴍᴀʟʟᴇʀ sɪᴢᴇs.")

@app.on_message(filters.command("setartist"))
async def set_artist(client, message: Message):
    global artist
    try:
        artist = message.text.split(" ", 1)[1]
        await message.reply(f"`Aʀᴛɪsᴛ sᴇᴛ ᴛᴏ: {artist}`")
    except IndexError:
        await message.reply("Pʟᴇᴀsᴇ sᴘᴇᴀᴋ ᴛʜᴇ ᴀʀᴛɪsᴛ ɴᴀᴍᴇ. Exᴀᴍᴘʟᴇ: `/setartist ᴅᴀʀᴋxsɪᴅᴇ`")

@app.on_message(filters.command("setauthor"))
async def set_author(client, message: Message):
    global author
    try:
        author = message.text.split(" ", 1)[1]
        await message.reply(f"Aᴜᴛʜᴏʀ sᴇᴛ ᴛᴏ: {author}")
    except IndexError:
        await message.reply("Pʟᴇᴀsᴇ sᴘᴇᴀᴋ ᴛʜᴇ ᴀᴜᴛʜᴏʀ ɴᴀᴍᴇ. Exᴀᴍᴘʟᴇ: `/setauthor ᴅᴀʀᴋxsɪᴅᴇ`")

@app.on_message(filters.command("settitle"))
async def set_title(client, message: Message):
    global video_title
    try:
        video_title = message.text.split(" ", 1)[1]
        await message.reply(f"Vɪᴅᴇᴏ ᴛɪᴛʟᴇ sᴇᴛ ᴛᴏ: {video_title}")
    except IndexError:
        await message.reply("Pʟᴇᴀsᴇ sᴘᴇᴀᴋ ᴛʜᴇ ᴠɪᴅᴇᴏ ᴛɪᴛʟᴇ. Exᴀᴍᴘʟᴇ: `/settitle [S1-01] Bunny Girl Senpai [720p] [Dual] @GenAnimeOfc`")

@app.on_message(filters.command("setsubtitle"))
async def set_subtitle(client, message: Message):
    global subtitle_title
    try:
        subtitle_title = message.text.split(" ", 1)[1]
        await message.reply(f"Sᴜʙᴛɪᴛʟᴇ ᴛɪᴛʟᴇ sᴇᴛ ᴛᴏ: {subtitle_title}")
    except IndexError:
        await message.reply("Pʟᴇᴀsᴇ sᴘᴇᴀᴋ ᴛʜᴇ sᴜʙᴛɪᴛʟᴇ ᴛɪᴛʟᴇ. Exᴀᴍᴘʟᴇ: `/setsubtitle Tʀᴀᴄᴋ`")

@app.on_message(filters.command("encoding"))
async def set_encoding(client, message: Message):
    global encoding_type
    try:
        new_encoding = message.text.split(" ", 1)[1]
        if new_encoding in ENCODING_FORMATS:
            encoding_type = ENCODING_FORMATS[new_encoding]
            await message.reply(f"Eɴᴄᴏᴅɪɴɢ ᴛʏᴘᴇ sᴇᴛ ᴛᴏ {new_encoding}.")
        else:
            await message.reply("Uɴsᴜᴘᴘᴏʀᴛᴇᴅ ᴇɴᴄᴏᴅɪɴɢ ᴛʏᴘᴇ. Aᴠᴀɪʟᴀʙʟᴇ ᴏᴘᴛɪᴏɴs: " + ", ".join(ENCODING_FORMATS.keys()))
    except IndexError:
        await message.reply("Pʟᴇᴀsᴇ sᴘᴇᴀᴋ ᴛʜᴇ ᴇɴᴄᴏᴅɪɴɢ ᴛʏᴘᴇ. Exᴀᴍᴘʟᴇ: `/encoding h265`")

@app.on_message(filters.command("quality"))
async def set_quality(client, message: Message):
    global quality
    try:
        new_quality = message.text.split(" ", 1)[1]
        if new_quality in QUALITY_RESOLUTIONS:
            quality = new_quality
            await message.reply(f"Qᴜᴀʟɪᴛʏ sᴇᴛ ᴛᴏ {new_quality}.")
        else:
            await message.reply("Uɴsᴜᴘᴘᴏʀᴛᴇᴅ ǫᴜᴀʟɪᴛʏ. Aᴠᴀɪʟᴀʙʟᴇ ᴏᴘᴛɪᴏɴs: " + ", ".join(QUALITY_RESOLUTIONS.keys()))
    except IndexError:
        await message.reply("Pʟᴇᴀsᴇ sᴘᴇᴀᴋ ᴛʜᴇ ǫᴜᴀʟɪᴛʏ. Exᴀᴍᴘʟᴇ: `/quality 720p`")

@app.on_message(filters.command("encode"))
async def start_encoding(client, message: Message):
    if message.reply_to_message:
        file = message.reply_to_message.video or message.reply_to_message.document
        if file:
            file_path = await file.download(file_name=DOWNLOAD_DIR + file.file_name)
            output_path = f"{DOWNLOAD_DIR}encoded_{file.file_name}"
            
            encoding_queue.put({"input_file": file_path, "output_file": output_path, "message": message})
            
            await process_queue()
        else:
            await message.reply("Pʟᴇᴀsᴇ rᴇᴘʟʏ ᴡɪᴛʜ ᴀ ᴠɪᴅᴇᴏ ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.")
    else:
        await message.reply("Pʟᴇᴀsᴇ rᴇᴘʟʏ ᴡɪᴛʜ ᴏʀɪɢɪɴᴀʟ ᴠɪᴅᴇᴏ.")

if __name__ == "__main__":
    app.run()

