import os
from pathlib import Path
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError

def gcs_manager(parameters=None, player=None, **kwargs):
    """
    Manage Google Cloud Storage (GCS) buckets and files.
    """
    if isinstance(parameters, str):
        parameters = {"action": "list_buckets"}
    if not isinstance(parameters, dict):
        return "Error: Invalid parameters format."

    action = parameters.get("action", "list_buckets").lower()
    
    try:
        client = storage.Client()
    except DefaultCredentialsError:
        return "Error: Google Cloud credentials not found. Run 'gcloud auth application-default login' in terminal to authenticate."
    except Exception as e:
        return f"Error initializing GCS Client: {str(e)}"

    try:
        if action == "list_buckets":
            buckets = list(client.list_buckets())
            if not buckets:
                return "No GCS buckets found in the active project."
            lines = ["### Google Cloud Storage Buckets:"]
            for b in buckets:
                lines.append(f"- **{b.name}** (Location: {b.location}, Storage Class: {b.storage_class})")
            return "\n".join(lines)

        elif action == "list_files":
            bucket_name = parameters.get("bucket_name", "").strip()
            if not bucket_name:
                return "Error: Missing required field: bucket_name"
            
            bucket = client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(max_results=100))
            if not blobs:
                return f"No files found in bucket '{bucket_name}'."
            
            lines = [f"### Files in bucket '{bucket_name}':"]
            for b in blobs:
                size_kb = round(b.size / 1024, 2)
                lines.append(f"- **{b.name}** ({size_kb} KB) | Last Modified: {b.updated}")
            return "\n".join(lines)

        elif action == "upload":
            bucket_name = parameters.get("bucket_name", "").strip()
            source_file = parameters.get("source_file", "").strip()
            destination_blob = parameters.get("destination_blob", "").strip()

            if not bucket_name or not source_file or not destination_blob:
                return "Error: Missing required fields: bucket_name, source_file, destination_blob"

            local_path = Path(source_file)
            if not local_path.exists():
                return f"Error: Local file '{source_file}' does not exist."

            bucket = client.bucket(bucket_name)
            blob = bucket.blob(destination_blob)
            
            if player:
                player.write_log(f"[GCS] Uploading {local_path.name} to gs://{bucket_name}/{destination_blob}")
                
            blob.upload_from_filename(str(local_path))
            return f"Successfully uploaded '{local_path.name}' to **gs://{bucket_name}/{destination_blob}**!"

        elif action == "download":
            bucket_name = parameters.get("bucket_name", "").strip()
            destination_blob = parameters.get("destination_blob", "").strip()
            destination_file = parameters.get("destination_file", "").strip()

            if not bucket_name or not destination_blob or not destination_file:
                return "Error: Missing required fields: bucket_name, destination_blob, destination_file"

            local_path = Path(destination_file)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            bucket = client.bucket(bucket_name)
            blob = bucket.blob(destination_blob)

            if not blob.exists():
                return f"Error: File '{destination_blob}' not found in bucket '{bucket_name}'."

            if player:
                player.write_log(f"[GCS] Downloading gs://{bucket_name}/{destination_blob} to {destination_file}")

            blob.download_to_filename(str(local_path))
            return f"Successfully downloaded file to **{local_path.resolve()}**!"

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        return f"GCS Error: {str(e)}"
