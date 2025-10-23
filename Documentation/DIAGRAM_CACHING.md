# Diagram POST Caching Implementation

This feature replaces the URL-encoded GET approach for diagram generation with POST requests and local filesystem caching.

## Changes Overview

### New Files
- `diagramm_proxy/__init__.py` - Module initialization
- `diagramm_proxy/diagram_cache.py` - Caching logic and POST request handling
- `abschnitte/management/commands/clear_diagram_cache.py` - Management command for cache clearing

### Modified Files
- `abschnitte/utils.py` - Updated `render_textabschnitte()` to use caching
- `.gitignore` - Added cache directory exclusion

## Configuration Required

Add to your Django settings file (e.g., `VorgabenUI/settings.py`):

```python
# Diagram cache settings
DIAGRAM_CACHE_DIR = 'diagram_cache'  # relative to MEDIA_ROOT

# Ensure MEDIA_ROOT and MEDIA_URL are configured
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

### URL Configuration

Ensure media files are served in development. In your main `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

# ... existing urlpatterns ...

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## How It Works

1. When a diagram is rendered, the system computes a SHA256 hash of the diagram content
2. It checks if a cached SVG exists for that hash
3. If cached: serves the existing file
4. If not cached: POSTs content to Kroki server, saves the response, and serves it
5. Diagrams are served from `MEDIA_URL/diagram_cache/{type}/{hash}.svg`

## Benefits

- **No URL length limitations** - Content is POSTed instead of URL-encoded
- **Improved performance** - Cached diagrams are served directly from filesystem
- **Reduced server load** - Kroki server is only called once per unique diagram
- **Persistent cache** - Survives application restarts
- **Better error handling** - Graceful fallback on generation failures

## Usage

### Viewing Diagrams
No changes required - diagrams will be automatically cached on first render.

### Clearing Cache

Clear all cached diagrams:
```bash
python manage.py clear_diagram_cache
```

Clear diagrams of a specific type:
```bash
python manage.py clear_diagram_cache --type plantuml
python manage.py clear_diagram_cache --type mermaid
```

## Testing

1. Create or view a page with diagrams
2. Verify diagrams render correctly
3. Check that `media/diagram_cache/` directory is created with cached SVGs
4. Refresh the page - second load should be faster (cache hit)
5. Check logs for cache hit/miss messages
6. Test cache clearing command

## Migration Notes

- Existing diagrams will be regenerated on first view after deployment
- The old URL-based approach is completely replaced
- No database migrations needed
- Ensure `requests` library is installed (already in requirements.txt)

## Troubleshooting

### Diagrams not rendering
- Check that MEDIA_ROOT and MEDIA_URL are configured correctly
- Verify Kroki server is accessible at `http://svckroki:8000`
- Check application logs for error messages
- Ensure media directory is writable

### Cache not working
- Verify Django storage configuration
- Check file permissions on media/diagram_cache directory
- Review logs for cache-related errors
