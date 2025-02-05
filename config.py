# BOT Credentials
API_ID = 20604892
API_HASH = "a75d4dab1a2483a157d93e3ae9bf7500"
BOT_TOKEN = "7146170095:AAHUSLQfrH-nYXg1iOB1kgsAi7BBqkVWtfk"

MONGO_URI = "mongodb+srv://nitinkumardhundhara:DARKXSIDE78@cluster0.wdive.mongodb.net/?retryWrites=true&w=majority"
MONGO_COLLECTION_NAME = "LuffyEncoder"
MONGO_DB_NAME = "User"

# Audio compression settings
AUDIO_BITRATE = "32k"  
AUDIO_FORMAT = "mp3" 
AUDIO_CHANNELS = 1     
AUDIO_SAMPLE_RATE = 44100  

# Video compression settings
VIDEO_SCALE = "min(640,iw):min(480,ih)"  
VIDEO_FPS = 24  # Standard frame rate for anime
VIDEO_CODEC = "libx265"  # Use libx265 for efficient compression
VIDEO_BITRATE = "600k"  # Increased bitrate for better quality, can adjust as needed
VIDEO_CRF = 20  # Lower CRF for high-quality output (20 is a good balance)
VIDEO_PRESET = "fast"  # Use 'fast' for a balance between speed and efficiency
VIDEO_PIXEL_FORMAT = "yuv420p"  # Standard pixel format for compatibility
VIDEO_PROFILE = "main"  # Main profile for better compatibility
VIDEO_AUDIO_CODEC = "aac"  # Audio codec
VIDEO_AUDIO_BITRATE = "128k"  # Better audio quality for anime
VIDEO_AUDIO_CHANNELS = 2  # Stereo audio for improved sound
VIDEO_AUDIO_SAMPLE_RATE = 44100  # Standard sample rate  
VIDEO_SCALE = "640:480"

# Temporary file settings
TEMP_FILE_SUFFIX_AUDIO = ".mp3"  
TEMP_FILE_SUFFIX_VIDEO = ".mp4"
TEMP_FILE_SUFFIX_VIDEO_MKV = ".mkv"  # Add this line if necessary
