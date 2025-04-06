from google.cloud import storage
import os
from pathlib import Path

def init_storage_client():
    """Initialize Google Cloud Storage client."""
    return storage.Client()

def upload_bag_file(bucket_name: str, source_file_path: str, destination_blob_name: str):
    """Upload a bag file to Google Cloud Storage."""
    client = init_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_path)
    print(f"File {source_file_path} uploaded to {destination_blob_name}.")

def download_bag_file(bucket_name: str, source_blob_name: str, destination_file_path: str):
    """Download a bag file from Google Cloud Storage."""
    client = init_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
    blob.download_to_filename(destination_file_path)
    print(f"Downloaded {source_blob_name} to {destination_file_path}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["upload", "download"], required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--blob", required=True)
    args = parser.parse_args()

    if args.action == "upload":
        upload_bag_file(args.bucket, args.file, args.blob)
    else:
        download_bag_file(args.bucket, args.blob, args.file)