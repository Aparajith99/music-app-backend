import boto3
import json
import requests
import os
from urllib.parse import urlparse

s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "music-app-images-816553836520"

with open("2026a2_songs.json", "r") as f:
    songs = json.load(f)["songs"]

unique_images = {}
for song in songs:
    url = song["img_url"]
    filename = os.path.basename(urlparse(url).path)
    unique_images[filename] = url

print(f"Found {len(unique_images)} unique images")

for filename, url in unique_images.items():
    print(f"Downloading {filename}...")
    response = requests.get(url, timeout=10)
    
    s3.put_object(
        Bucket=BUCKET,
        Key=filename,
        Body=response.content,
        ContentType="image/jpeg"
    )
    print(f"Uploaded {filename}")

print("All images uploaded")
