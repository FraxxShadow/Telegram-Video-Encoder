import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN

app = Client("advancedVideoEncoderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "./downloads/"
ENCODING_FORMATS = {"h265": "libx265", "h264": "libx264"}
quality = "720p"  # Default quality setting
encoding_type = "libx264"  # Default encoding type
media_type = "video"  # Default media type
fps = None  # Default FPS setting (None means no change)

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

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("Bᴀᴋᴋᴀᴀ!!! 😜\nI ᴀᴍ ᴀ ᴠɪᴅᴇᴏ ᴇɴᴄᴏᴅᴇʀ ʙᴏᴛ ᴄʀᴇᴀᴛᴇᴅ ʙʏ @DARKXSIDE78 ᴛᴏ ᴇɴᴄᴏᴅᴇ ᴠɪᴅᴇᴏs ᴀɴᴅ ᴄᴏᴍᴘʀᴇss ᴛʜᴇᴍ ɪɴᴛᴏ sᴍᴀʟʟᴇʀ sɪᴢᴇs.")

def encode_video(input_file, output_file, encoding_type="libx265", resolution="720", fps=None):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"The input file does not exist: {input_file}")

    ffmpeg_cmd = [
        "ffmpeg", "-i", input_file, "-c:v", encoding_type, "-preset", "veryfast",
        "-crf", "27",  # Lower CRF for better quality
        "-aq-mode", "2", "-tune", "film",  # Film tuning for anime to enhance quality
        "-c:a", "libopus", "-b:a", "35k", "-b:v", "150k",  # Audio bitrate
        "-c:s", "copy",  # Copy subtitles
        "-vf", f"scale=-2:{resolution},unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=2",  # Sharpness filter
        "-map", "0",  # Stereo audio
        "-metadata:s:v", "title='[GenAnimeOfc]'",
        "-metadata:s:s", "title='[GenAnimeOfc]'",
        "-metadata:s:a", "title='[GenAnimeOfc]'",
        "-metadata", "title='GenAnimeOfc [t.me/GenAnimeOfc]'",
        "-metadata", "author='DARKXSIDE78'",
    ]

    if fps:
        ffmpeg_cmd.extend(["-r", str(fps)])  # Add FPS to the command if specified

    ffmpeg_cmd.append(output_file)

    print("Running ffmpeg command:", " ".join(ffmpeg_cmd))
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    else:
        print("FFmpeg output:", result.stdout)

@app.on_message(filters.command("fps"))
async def set_fps(client, message: Message):
    global fps
    try:
        fps_value = int(message.text.split(" ", 1)[1])
        if fps_value > 0:
            fps = fps_value
            await message.reply(f"Frame rate set to {fps} FPS.")
        else:
            await message.reply("FPS value must be greater than 0.")
    except (IndexError, ValueError):
        await message.reply("Please specify a valid FPS value. Example: `/fps 60`.")

@app.on_message(filters.command("mediatype"))
async def set_media_type(client, message: Message):
    global media_type
    try:
        new_media_type = message.text.split(" ", 1)[1].lower()
        if new_media_type in ["video", "document"]:
            media_type = new_media_type
            await message.reply(f"Media type set to {media_type}.")
        else:
            await message.reply("Invalid media type. Use `video` or `document`.")
    except IndexError:
        await message.reply("Please specify a media type. Example: `/mediatype video`.")

@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    await message.reply("Downloading...")
    download_path = await client.download_media(message, DOWNLOAD_DIR)
    if not os.path.exists(download_path):
        await message.reply("Failed to download the video.")
        return

    try:
        encoded_file = os.path.splitext(download_path)[0] + "_encoded" + os.path.splitext(download_path)[1]

        await message.reply("Encoding in progress, please wait...")

        resolution = QUALITY_RESOLUTIONS.get(quality, "720")
        encode_video(download_path, encoded_file, encoding_type=encoding_type, resolution=resolution, fps=fps)

        # Send encoded video based on media type
        if media_type == "video":
            await client.send_video(
                chat_id=message.chat.id,
                video=encoded_file,
                caption="Here's the encoded file."
            )
        else:
            await client.send_video(
                chat_id=message.chat.id,
                video=encoded_file,
                caption="Here's the encoded file."
            )

        await message.reply("Encoding complete!")

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)
        if os.path.exists(encoded_file):
            os.remove(encoded_file)

app.run()

