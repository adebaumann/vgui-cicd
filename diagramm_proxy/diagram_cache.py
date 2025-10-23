import hashlib
import os
import requests
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

# Configure cache directory
CACHE_DIR = getattr(settings, 'DIAGRAM_CACHE_DIR', 'diagram_cache')
KROKI_UPSTREAM = "http://svckroki:8000"

def get_cache_path(diagram_type, content_hash):
    """Generate cache file path for a diagram."""
    return os.path.join(CACHE_DIR, diagram_type, f"{content_hash}.svg")

def compute_hash(content):
    """Compute SHA256 hash of diagram content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_cached_diagram(diagram_type, diagram_content):
    """
    Retrieve diagram from cache or generate it via POST.
    
    Args:
        diagram_type: Type of diagram (e.g., 'plantuml', 'mermaid')
        diagram_content: Raw diagram content
        
    Returns:
        Path to cached diagram file (relative to MEDIA_ROOT)
    """
    content_hash = compute_hash(diagram_content)
    cache_path = get_cache_path(diagram_type, content_hash)
    
    # Check if diagram exists in cache
    if default_storage.exists(cache_path):
        logger.debug(f"Cache hit for {diagram_type} diagram: {content_hash[:8]}")
        return cache_path
    
    # Generate diagram via POST request
    logger.info(f"Cache miss for {diagram_type} diagram: {content_hash[:8]}, generating...")
    try:
        url = f"{KROKI_UPSTREAM}/{diagram_type}/svg"
        response = requests.post(
            url,
            data=diagram_content.encode('utf-8'),
            headers={'Content-Type': 'text/plain'},
            timeout=30
        )
        response.raise_for_status()
        
        # Ensure cache directory exists
        cache_dir = os.path.dirname(default_storage.path(cache_path))
        os.makedirs(cache_dir, exist_ok=True)
        
        # Save to cache
        default_storage.save(cache_path, ContentFile(response.content))
        logger.info(f"Diagram cached successfully: {cache_path}")
        
        return cache_path
        
    except requests.RequestException as e:
        logger.error(f"Error generating diagram: {e}")
        raise

def clear_cache(diagram_type=None):
    """
    Clear cached diagrams.
    
    Args:
        diagram_type: If specified, only clear diagrams of this type
    """
    if diagram_type:
        cache_path = os.path.join(CACHE_DIR, diagram_type)
    else:
        cache_path = CACHE_DIR
        
    if default_storage.exists(cache_path):
        full_path = default_storage.path(cache_path)
        # Walk through and delete files
        for root, dirs, files in os.walk(full_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted cached diagram: {file_path}")
                except OSError as e:
                    logger.error(f"Error deleting {file_path}: {e}")
