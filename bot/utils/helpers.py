# Empty helpers module for generic utility functions that may be needed later.
# For now, most utilities are in audio_utils or image_utils, and db in database/db.py

def clean_html(text: str) -> str:
    """Utility to clean html tags from strings if needed"""
    import re
    return re.sub(r'<[^>]*>', '', text)
