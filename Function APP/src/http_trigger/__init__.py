import logging
import os
import json
import azure.functions as func
from ..Common_functions.cosmos_helper import get_cosmos_container_client
from ..Common_functions.blob_helper import get_blob_service_client
from .cosmos_helper import fetch_cosmos_data_selected_ids, fetch_cosmos_data
from .blob_helper import get_summary_transcript_text


globallib_cosmos_container = os.getenv('GLOBALLIB_COSMOS_CONTAINER_NAME')
cosmos_key = os.getenv('COSMOS_KEY', None)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Global Videos list Function: Start')
    
    # Get parameters from query string or request body
    filtered_ids = req.params.get('filtered_ids')
    page_size = req.params.get('page_size', '20')
    continuation_token = req.params.get('continuation_token')
    
    if not filtered_ids:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        
        filtered_ids = req_body.get('filtered_ids')
        page_size = req_body.get('page_size', page_size)
        continuation_token = req_body.get('continuation_token', continuation_token)
    
    # Convert page_size to int
    try:
        page_size = int(page_size)
    except (ValueError, TypeError):
        page_size = 20
    
    cosmos_container_client = await get_cosmos_container_client(globallib_cosmos_container, cosmos_key)

    # Fetching the records from the cosmos db for selected Ids
    if filtered_ids:
        logging.info(f"Fetching records with selected id")
        cosmos_result = await fetch_cosmos_data_selected_ids(
            cosmos_container_client, 
            tuple(filtered_ids),
            page_size=page_size,
            continuation_token=continuation_token
        )
    else:
        logging.info("Fetching all the records from cosmos db")
        cosmos_result = await fetch_cosmos_data(
            cosmos_container_client,
            page_size=page_size,
            continuation_token=continuation_token
        )
    
    # Handle error case
    if isinstance(cosmos_result, str):
        return func.HttpResponse(cosmos_result, status_code=500, mimetype="application/json")
    
    cosmos_data = cosmos_result.get('items', [])
    next_token = cosmos_result.get('continuation_token')
    has_more = cosmos_result.get('has_more', False)
    
    logging.info(f"Total number of records in current page: {len(cosmos_data)}")
    
    # Initialize blob service client for transcript summary retrieval
    blob_service_client = await get_blob_service_client()
    
    # Fetch transcript summary for each video
    for index, video in enumerate(cosmos_data):
        video_id = video.get('VideoID')
        language = 'en-US'  # Default to 'en-US'
        folder_path = video.get('folder_path')
        logging.info(f"Processing video {index + 1}/{len(cosmos_data)}: VideoID={video_id}, Language={language}, FolderPath={folder_path}")
        
        if video_id and folder_path:
            try:
                logging.info(f"Fetching transcript summary for video {video_id} in language {language}")
                transcript_summary = await get_summary_transcript_text(
                    blob_service_client, 
                    video_id, 
                    language, 
                    blob_name=folder_path
                )
                logging.info(f"Transcript summary result: {bool(transcript_summary)} (length: {len(transcript_summary) if transcript_summary else 0})")
                
                if transcript_summary:
                    cosmos_data[index]['gist'] = transcript_summary
                    logging.info(f"Successfully added gist for video {video_id}")
                else:
                    logging.info(f"No gist found for video {video_id}")
            except Exception as e:
                logging.warning(f"Could not fetch gist for video {video_id}: {str(e)}")
        else:
            logging.warning(f"Skipping video - missing video_id or folder_path: VideoID={video_id}, FolderPath={folder_path}")

    if cosmos_data or has_more:
        # Prepare paginated response with continuation_token first
        response_data = {
            'continuation_token': next_token,
            'has_more': has_more,
            'page_size': page_size,
            'count': len(cosmos_data),
            'items': cosmos_data
        }
        
        return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")
    else:
        return func.HttpResponse(
            json.dumps({
                'continuation_token': None,
                'has_more': False,
                'page_size': page_size,
                'count': 0,
                'items': [],
                'message': 'No records found for global videos in cosmos db'
            }), 
            status_code=200, 
            mimetype="application/json"
        )