import requests
import time

ZAMZAR_API_KEY = "b791c20c9acc35b9812132d64facc47b7208f3cb"

async def convert_instagram_to_mp3(file_path):
    """Uploads an Instagram video to Zamzar and converts it to MP3."""
    
    upload_url = "https://sandbox.zamzar.com/v1/files"
    headers = {"Authorization": f"Basic {ZAMZAR_API_KEY}"}

    # ✅ 1. Upload Video File
    with open(file_path, "rb") as video_file:
        response = requests.post(upload_url, headers=headers, files={"file": video_file})

    if response.status_code != 201:
        return f"❌ Upload Error: {response.json().get('message', 'Unknown error')}"

    file_id = response.json()["id"]
    
    # ✅ 2. Request MP3 Conversion
    conversion_url = f"https://sandbox.zamzar.com/v1/jobs"
    convert_data = {"target_format": "mp3", "source_file": file_id}
    convert_response = requests.post(conversion_url, headers=headers, data=convert_data)

    if convert_response.status_code != 201:
        return f"❌ Conversion Error: {convert_response.json().get('message', 'Unknown error')}"

    job_id = convert_response.json()["id"]
    
    # ✅ 3. Wait for Conversion to Complete
    job_status_url = f"https://sandbox.zamzar.com/v1/jobs/{job_id}"
    
    for _ in range(10):  # Check status 10 times with delays
        job_status = requests.get(job_status_url, headers=headers).json()
        if job_status["status"] == "successful":
            break
        time.sleep(5)  # Wait before checking again

    # ✅ 4. Get MP3 Download Link
    for target_file in job_status.get("target_files", []):
        mp3_file_id = target_file["id"]
        mp3_download_url = f"https://sandbox.zamzar.com/v1/files/{mp3_file_id}/content"
        return mp3_download_url  # ✅ Return MP3 link
    
    return "❌ MP3 conversion failed. Please try again later."
