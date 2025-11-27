import logging
import re
from typing import List, Dict, Union, Any
from azure.cosmos import ContainerProxy


def remove_file_extension(data: Any) -> Any:
    """
    Removes file extensions (.mp4, .avi, .mov, .mkv, .wmv, .flv, .webm, .m4v) from video_file_name fields.
    
    Args:
        data: Can be a string, dictionary, or list containing video file information
        
    Returns:
        The same data structure with file extensions removed from video_file_name fields
    """
    if isinstance(data, str):
        # Remove video file extensions from string
        return re.sub(r'\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v)$', '', data, flags=re.IGNORECASE)
    
    elif isinstance(data, dict):
        # Create a copy to avoid modifying the original
        result = data.copy()
        
        # Process video_file_name field if it exists
        if 'video_file_name' in result and isinstance(result['video_file_name'], str):
            result['video_file_name'] = re.sub(r'\.(mp4|avi|mov|mkv|wmv|flv|webm|m4v)$', '', result['video_file_name'], flags=re.IGNORECASE)
        
        # Recursively process nested dictionaries and lists
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                result[key] = remove_file_extension(value)
        
        return result
    
    elif isinstance(data, list):
        # Process each item in the list
        return [remove_file_extension(item) for item in data]
    
    else:
        # Return unchanged for other data types
        return data


async def fetch_cosmos_data_selected_ids(container: ContainerProxy, list_of_ids: List[str], page_size: int = 20, continuation_token: str = None) -> Union[Dict, str]:
    """
    Fetches data from a Cosmos DB container for a list of video IDs with pagination.
    
    Args:
        container: The Cosmos DB container object to query.
        list_of_ids: A list of video IDs to filter results. Can be a single ID or multiple IDs.
        page_size: Number of items to return per page (default: 20)
        continuation_token: Token for fetching the next page (default: None)
    
    Returns:
        Union[Dict, str]: A dictionary containing 'items' (list of documents), 'continuation_token' (for next page),
                         'has_more' (boolean), or an error message if an exception occurs.
    
    Raises:
        No exceptions are raised as they are caught internally.
    """
    try:
        if len(list_of_ids) > 1:
            query = f"SELECT * FROM c where c.VideoID in {list_of_ids}"
        else:
            query = f"SELECT * FROM c where c.VideoID = '{list_of_ids[0]}'"
        
        items = []
        query_iterable = container.query_items(
            query=query,
            enable_cross_partition_query=True,
            max_item_count=page_size
        )
        
        # Get iterator with continuation support
        pages = query_iterable.by_page(continuation_token=continuation_token)
        
        # Get only the first page
        page = await pages.__anext__()
        async for item in page:
            items.append(item)
        
        # Get continuation token for next page
        next_token = pages.continuation_token
        
        return {
            'continuation_token': next_token,
            'has_more': next_token is not None,
            'page_size': page_size,
            'count': len(items),
            'items': remove_file_extension(items)
        }
    except Exception as e:  
        logging.info(f'Exception in fetch cosmos data selected ids function: {e}')
        return "Error in fetching the data for selected id's from cosmos db"


async def fetch_cosmos_data(container: ContainerProxy, page_size: int = 20, continuation_token: str = None) -> Union[Dict, str]:
    """
    Fetches indexed video data from Cosmos DB container with pagination.
    
    This function queries the Cosmos DB container for videos with
    VideoIndexedStatus set to 'IndexingFinished' or 'ReindexingFinished' and returns specific fields
    from the matching documents with pagination support.
    
    Args:
        container (ContainerProxy): A Cosmos DB container proxy object to query against
        page_size (int): Number of items to return per page (default: 20)
        continuation_token (str): Token for fetching the next page (default: None)
    
    Returns:
        Union[Dict, str]: On success, returns a dictionary containing 'items' (list of video metadata),
                         'continuation_token' (for next page), and 'has_more' (boolean).
                         On failure, returns an error message as a string.
    
    Raises:
        Exception: Function catches all exceptions and returns error message instead of raising
    """
    
    try:
        query = f"SELECT c.VideoID, c.video_file_name, c.thumbnail_image, c.folder_path, c.container_name, c.video_info, c.video_indexer_start, c._ts FROM c WHERE (c.VideoIndexedStatus = 'IndexingFinished' AND c.operation_status = 'Success') OR (c.VideoIndexedStatus = 'ReindexingFinished' AND c.operation_status = 'Success') ORDER BY c._ts DESC"
        
        items = []
        query_iterable = container.query_items(
            query=query,
            enable_cross_partition_query=True,
            max_item_count=page_size
        )
        
        # Get iterator with continuation support
        pages = query_iterable.by_page(continuation_token=continuation_token)
        
        # Get only the first page
        page = await pages.__anext__()
        async for item in page:
            items.append(item)
        
        # Get continuation token for next page
        next_token = pages.continuation_token
        
        return {
            'continuation_token': next_token,
            'has_more': next_token is not None,
            'page_size': page_size,
            'count': len(items),
            'items': remove_file_extension(items)
        }
    except Exception as e:
        logging.info(f'Exception in fetch cosmos data function: {e}')
        return "Error in fetching the data from cosmos db"


cosmos helper.py