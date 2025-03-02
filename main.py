import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN

app = Client("advancedVideoEncoderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "./downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

resolution = "1920:1080"

def encode_video(input_file, output_file, resolution):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"The input file does not exist: {input_file}")

    output_file = os.path.splitext(output_file)[0] + ".mkv"
    ffmpeg_cmd = [
        "ffmpeg", "-i", input_file,
        "-map", "0:v", "-map", "0:a", "-map", "0:s?",
        "-c:v", "libx265", "-crf", "27",
        "-vf", f"scale={resolution}",
        "-c:s", "copy", "-pix_fmt", "yuv420p",
        "-b:v", "160k", "-c:a", "libopus", "-b:a", "60k",
        "-preset", "superfast", "-threads", "0",
        "-metadata", "title=GenAnimeOfc [t.me/GenAnimeOfc]",
        "-metadata:s:s", "title=[GenAnimeOfc]",
        "-metadata:s:a", "title=[GenAnimeOfc]",
        "-metadata", "author=DARKXSIDE78",
        "-metadata:s:v", "title=[GenAnimeOfc]",
        output_file
    ]

    print("Running ffmpeg command:", " ".join(ffmpeg_cmd))
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    else:
        print("FFmpeg output:", result.stdout)
    
    return output_file

@app.on_message(filters.command("resolution"))
async def set_resolution(client, message: Message):
    global resolution
    try:
        new_resolution = message.text.split(" ", 1)[1]
        resolution = new_resolution
        await message.reply(f"Resolution set to {resolution}.")
    except IndexError:
        await message.reply("Please specify a resolution. Example: `/resolution 1280:720`.")

@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    await message.reply("Downloading...")
    download_path = await client.download_media(message, DOWNLOAD_DIR)
    if not os.path.exists(download_path):
        await message.reply("Failed to download the video.")
        return

    try:
        encoded_file = os.path.splitext(download_path)[0] + "_encoded.mkv"

        await message.reply("Encoding in progress, please wait...")
        encoded_file = encode_video(download_path, encoded_file, resolution)

        thumb_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
        if not os.path.exists(thumb_path):
            await client.download_media(message.video.thumbs[0], thumb_path)
        
        await client.send_document(
            chat_id=message.chat.id,
            document=encoded_file,
            thumb=thumb_path,
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
