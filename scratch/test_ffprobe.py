import asyncio
from pathlib import Path
import json

async def get_video_metadata(video_path: Path) -> tuple:
    """Returns (duration, width, height) of the video file using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(video_path)
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            data = json.loads(stdout.decode('utf-8'))
            duration = None
            width = None
            height = None
            
            if "format" in data and "duration" in data["format"]:
                try: duration = int(float(data["format"]["duration"]))
                except ValueError: pass
                
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    if "width" in stream:
                        width = int(stream["width"])
                    if "height" in stream:
                        height = int(stream["height"])
                    if not duration and "duration" in stream:
                        try: duration = int(float(stream["duration"]))
                        except ValueError: pass
                    break
            return duration, width, height
    except Exception as e:
        print(f"Failed: {e}")
    return None, None, None

async def main():
    video_path = Path("test_video.mp4")
    duration, width, height = await get_video_metadata(video_path)
    print(f"Probed Metadata -> Duration: {duration}s, Width: {width}px, Height: {height}px")

asyncio.run(main())
