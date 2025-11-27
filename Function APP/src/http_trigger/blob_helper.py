import logging
import json
from azure.storage.blob import BlobServiceClient
from  typing import Optional, Dict, Any
import os

container_name = os.getenv("BLOB_METADATA_CONTAINER_NAME")

async def get_summary_transcript_text(blob_client: BlobServiceClient, video_id: str, language: str, blob_name: Optional[str] = None) -> str:

    # Define filename patterns to try
    filename_patterns = []
    
    # Pattern 1: {blob_name}_{video_id}_transcript.json (if blob_name provided)
    if blob_name:
        blob_name = os.path.splitext(blob_name)[0] # Remove file extension if present
        logging.info(blob_name)
        gist_pattern1 = f"{blob_name}_{video_id}_{language}_gist_summary_transcript.txt"
        filename_patterns.append(gist_pattern1)
        logging.info(f"Added gist pattern 1: {gist_pattern1}")

    # Pattern 2: {video_id}_transcript.json
    gist_pattern2 = f"{blob_name}_{video_id}_gist_summary_transcript.txt"
    filename_patterns.append(gist_pattern2)
    logging.info(f"Added gist pattern 2: {gist_pattern2}")
    logging.info(f"Searching for transcript in container '{container_name}' with {len(filename_patterns)} pattern(s)")
    
    # Try each filename pattern
    for index, filename in enumerate(filename_patterns):
        try:
            logging.info(f"Attempting pattern {index + 1}: {filename}")
            
            # Get blob client for this specific file
            blob_client_file = blob_client.get_blob_client(
                container=container_name,
                blob=filename
            )
            
            # Check if blob exists and get properties
            logging.info(f"Checking if blob exists: {filename}")
            blob_properties = blob_client_file.get_blob_properties()
            
            # Download blob content
            logging.info(f"Downloading blob content: {filename}")
            blob_data = blob_client_file.download_blob()
            summary_transcript = blob_data.readall().decode('utf-8')
            return summary_transcript
        except Exception as e:
            logging.info(f"Pattern {index + 1} not found: {filename}")
            continue
    logging.info("No transcript found for any of the specified patterns.")
    return {}


blobhelper.py