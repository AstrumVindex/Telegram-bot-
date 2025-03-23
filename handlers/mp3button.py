import requests
import json
import os
import base64
import instaloader
import subprocess
from instaloader import Post

# ✅ Initialize Instaloader
L = instaloader.Instaloader()

# ✅ Replace with your actual Zamzar API key
ZAMZAR_API_KEY = "a85697ca1f1b8fe6e2a04c6405517cfdf6a2891f"

async def get_instagram_video_url(instagram_url):
    """Extracts the direct video URL from an Instagram post using Instaloader."""
    try:
        shortcode = instagram_url.strip("/").split("/")[-1]  # Extract shortcode from URL
        post = Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            return post.video_url  # ✅ Return direct video URL
        else:
            return None
    except Exception as e:
        print("❌ Error getting Instagram video URL:", e)
        return None

async def download_instagram_video(instagram_url):
    """Downloads the Instagram video locally."""
    try:
        # ✅ Step 1: Extract the direct video URL
        direct_video_url = await get_instagram_video_url(instagram_url)
        if not direct_video_url:
            return None  # ❌ Video extraction failed

        response = requests.get(direct_video_url, stream=True)
        if response.status_code == 200:
            file_path = "instagram_video.mp4"
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            print(f"✅ Video downloaded successfully: {file_path}")  # Debug log
            return file_path
        else:
            print("❌ Failed to download Instagram video.")
            return None
    except Exception as e:
        print("❌ Download Error:", e)
        return None

async def compress_video(input_path, output_path):
    """Compress video using FFmpeg to reduce file size under 1MB."""
    try:
        # ✅ Compress the video to reduce size below 1MB
        cmd = f'ffmpeg -i "{input_path}" -vf "scale=-2:360" -b:v 500k -c:v libx264 -preset slow -c:a aac -strict -2 "{output_path}"'
        subprocess.run(cmd, shell=True, check=True)

        # ✅ Check compressed file size
        compressed_size = os.path.getsize(output_path)
        print(f"✅ Compressed Video Size: {compressed_size / 1024} KB")

        if compressed_size > 1048576:  # Zamzar free plan limit (1MB)
            print("❌ Still too large! Compression failed.")
            return None

        return output_path
    except Exception as e:
        print("❌ Compression Error:", e)
        return None

async def convert_instagram_to_mp3(instagram_url):
    """Downloads an Instagram video, compresses it, uploads it to Zamzar, and converts it to MP3."""
    try:
        # ✅ Step 1: Download Instagram video
        video_path = await download_instagram_video(instagram_url)
        if not video_path:
            return "❌ Failed to download video."

        # ✅ Step 2: Compress Video Before Uploading
        compressed_video_path = "compressed_instagram_video.mp4"
        compressed_video = await compress_video(video_path, compressed_video_path)

        if not compressed_video:
            return "❌ Video compression failed!"

        # ✅ Step 3: Zamzar API authentication
        auth_header = base64.b64encode(f"{ZAMZAR_API_KEY}:".encode()).decode()

        # ✅ Step 4: Upload video file to Zamzar
        upload_url = "https://api.zamzar.com/v1/files"
        headers = {"Authorization": f"Basic {auth_header}"}

        with open(compressed_video_path, "rb") as video_file:
            files = {"content": video_file}  # ✅ Use "content" instead of "file"
            upload_response = requests.post(upload_url, headers=headers, files=files)

        if upload_response.status_code != 201:
            print(f"❌ Zamzar Upload Failed: {upload_response.text}")  # Debug log
            return "❌ Zamzar upload failed."

        upload_response_json = upload_response.json()
        print("🔹 Zamzar Upload Response:", json.dumps(upload_response_json, indent=4))

        if "id" not in upload_response_json:
            return f"❌ Upload Error: {upload_response_json.get('message', 'Failed to upload video.')}"

        file_id = upload_response_json["id"]

        # ✅ Step 5: Create a conversion job
        job_url = "https://api.zamzar.com/v1/jobs"
        payload = {
            "source_file": file_id,  # ✅ Use file_id from previous step
            "target_format": "mp3"
        }

        job_response = requests.post(job_url, headers=headers, json=payload).json()
        print("🔹 Zamzar Conversion Response:", json.dumps(job_response, indent=4))

        if "id" not in job_response:
            return f"❌ Conversion Error: {job_response.get('message', 'Failed to create conversion job.')}"

        job_id = job_response["id"]

        # ✅ Step 6: Poll status until the conversion is complete
        status_url = f"https://api.zamzar.com/v1/jobs/{job_id}"

        while True:
            status_response = requests.get(status_url, headers=headers).json()
            if status_response["status"] == "successful":
                break
            elif status_response["status"] == "failed":
                return "❌ Conversion failed!"
            
            print("⏳ Waiting for conversion to complete...")

        # ✅ Step 7: Get the MP3 download link
        mp3_url = status_response["target_files"][0]["url"]

        # ✅ Cleanup: Delete temporary files
        os.remove(video_path)
        os.remove(compressed_video_path)

        return mp3_url

    except Exception as e:
        return f"❌ API Error: {str(e)}"
