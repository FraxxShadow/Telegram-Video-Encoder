import os
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN

app = Client("advancedVideoEncoderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "./downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Global encoding settings
resolution = "1920:1080"  
encoding_mode = "single"  # Options: "parallel" or "single"

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
        "-b:v", "150k", "-c:a", "libopus", "-b:a", "50k",
        "-preset", "superfast", "-threads", "0",
        "-metadata", "title=GenAnimeOfc [t.me/GenAnimeOfc]",
        "-metadata:s:s", "title=[GenAnimeOfc]",
        "-metadata:s:a", "title=[GenAnimeOfc]",
        "-metadata", "author=DARKXSIDE78",
        "-metadata:s:v", "title=[GenAnimeOfc]",
        output_file
    ]
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while process.poll() is None:
        line = process.stderr.readline()
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {process.stderr.read()}")
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

@app.on_message(filters.command("setquality"))
async def set_quality(client, message: Message):
    global resolution
    options = {"low": "854:480", "medium": "1280:720", "high": "1920:1080"}
    try:
        quality = message.text.split(" ", 1)[1].lower()
        resolution = options.get(quality, "1280:720")
        await message.reply(f"Quality set to {resolution}.")
    except IndexError:
        await message.reply("Use /setquality low, medium, or high.")

@app.on_message(filters.command("encmode"))
async def set_encoding_mode(client, message: Message):
    global encoding_mode
    try:
        new_mode = message.text.split(" ", 1)[1].lower()
        if new_mode in ["parallel", "single"]:
            encoding_mode = new_mode
            await message.reply(f"Encoding mode set to {encoding_mode}.")
        else:
            await message.reply("Invalid mode! Use `parallel` or `single`.")
    except IndexError:
        await message.reply("Please specify an encoding mode. Example: `/encmode parallel`.")

queue = []
processing = False

async def process_queue():
    global processing
    while queue:
        processing = True
        task = queue.pop(0)
        await task()
    processing = False

async def handle_encoding_single(client, message, download_path):
    await message.reply("Encoding in progress, please wait...")
    output_file = os.path.splitext(download_path)[0] + "_encoded.mkv"
    encoded_file = await asyncio.to_thread(encode_video, download_path, output_file, resolution)
    
    await message.reply("Uploading...")
    await client.send_document(
        chat_id=message.chat.id,
        document=encoded_file,
        caption="Here is your encoded video!"
    )
    os.remove(download_path)
    os.remove(encoded_file)

async def handle_encoding_parallel(client, message, download_path):
    await message.reply("Encoding in parallel (480p, 720p, 1080p), please wait...")
    target_resolutions = {
        "480p": "854:480",
        "720p": "1280:720",
        "1080p": "1920:1080"
    }
    tasks = []
    for label, res in target_resolutions.items():
        out_file = os.path.splitext(download_path)[0] + f"_{label}.mkv"
        task = asyncio.to_thread(encode_video, download_path, out_file, res)
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for label, result in zip(target_resolutions.keys(), results):
        if isinstance(result, Exception):
            await message.reply(f"Error encoding {label}: {result}")
        else:
            await message.reply(f"Uploading {label} version...")
            await client.send_document(
                chat_id=message.chat.id,
                document=result,
                caption=f"Encoded {label} version"
            )
            if os.path.exists(result):
                os.remove(result)
    os.remove(download_path)

@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    progress_msg = await message.reply("Downloading: 0%")

    async def download_progress(current, total, speed=None):
        percent = (current / total) * 100
        speed_kbps = (speed / 1024) if speed else 0  # Convert speed to KB/s, handle None case
        text = f"Downloading: {percent:.1f}% ({current}/{total} bytes) at {speed_kbps:.1f} KB/s"
        try:
            await progress_msg.edit_text(text)
        except Exception:
            pass


    download_path = await client.download_media(message, DOWNLOAD_DIR, progress=download_progress)
    if not os.path.exists(download_path):
        await message.reply("Failed to download the video.")
        return

    await message.reply("Download complete, starting encoding...")
    if encoding_mode == "parallel":
        asyncio.create_task(handle_encoding_parallel(client, message, download_path))
    else:
        queue.append(lambda: handle_encoding_single(client, message, download_path))
        if not processing:
            asyncio.create_task(process_queue())

app.run()
