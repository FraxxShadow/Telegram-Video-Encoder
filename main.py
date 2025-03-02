import os
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN

app = Client("advancedVideoEncoderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "./downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

resolution = "1920:1080"

def get_duration(input_file):
    """Return duration (in seconds) of the input file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    return float(output.strip())

async def encode_video(input_file, output_file, resolution, progress_callback=None):
    """Asynchronously run ffmpeg with -progress to report encoding progress."""
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
        "-progress", "pipe:1",
        output_file
    ]
    print("Running ffmpeg command:", " ".join(ffmpeg_cmd))
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        text=True
    )
    
    # Parse progress output line by line
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        if progress_callback:
            await progress_callback(line.strip())
    await process.wait()
    if process.returncode != 0:
        stderr = await process.stderr.read()
        raise RuntimeError(f"FFmpeg error: {stderr}")
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
    # Download progress
    download_msg = await message.reply("Downloading progress: 0%")
    async def download_progress(current, total):
        percent = (current / total) * 100
        try:
            await download_msg.edit_text(f"Downloading progress: {percent:.1f}%")
        except Exception:
            pass

    download_path = await client.download_media(message, DOWNLOAD_DIR, progress=download_progress)
    if not os.path.exists(download_path):
        await message.reply("Failed to download the video.")
        return

    try:
        encoded_file = os.path.splitext(download_path)[0] + "_encoded.mkv"
        # Get duration for encoding progress calculation
        duration = get_duration(download_path)
        
        progress_msg = await message.reply("Encoding progress: 0%")
        async def encoding_progress(line):
            # ffmpeg outputs lines like "out_time=00:00:05.00"
            if line.startswith("out_time="):
                out_time_str = line.split("=")[1].strip()
                try:
                    h, m, s = out_time_str.split(":")
                    current_time = int(h) * 3600 + int(m) * 60 + float(s)
                    percent = (current_time / duration) * 100
                    try:
                        await progress_msg.edit_text(f"Encoding progress: {percent:.1f}%")
                    except Exception:
                        pass
                except Exception:
                    pass
        
        await message.reply("Encoding in progress, please wait...")
        encoded_file = await encode_video(download_path, encoded_file, resolution, progress_callback=encoding_progress)
        
        # Handle thumbnail: download if not exists
        thumb_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
        if not os.path.exists(thumb_path):
            if hasattr(message.video, "thumbnails") and message.video.thumbnails:
                thumb_path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
                await client.download_media(message.video.thumbnails[0].file_id, thumb_path)
        
        upload_msg = await message.reply("Uploading progress: 0%")
        async def upload_progress(current, total):
            percent = (current / total) * 100
            try:
                await upload_msg.edit_text(f"Uploading progress: {percent:.1f}%")
            except Exception:
                pass
        
        await client.send_document(
            chat_id=message.chat.id,
            document=encoded_file,
            thumb=thumb_path,
            caption="Here's the encoded file.",
            progress=upload_progress
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
