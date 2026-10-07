import re
import urllib.parse
from typing import Optional, Tuple


def is_share_link(url: str) -> bool:
    """Checks if a URL points to Google Drive or Dropbox."""
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return "drive.google.com" in hostname or "dropbox.com" in hostname


def resolve_share_link(url: str) -> str:
    """
    Transforms Google Drive or Dropbox sharing links into direct download links.
    Returns the resolved direct URL (or original URL if not recognized).
    """
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()

    # 1. Dropbox link conversion
    if "dropbox.com" in hostname:
        # If it's dropbox.com, ensure dl=1
        query_params = urllib.parse.parse_qs(parsed.query)
        query_params["dl"] = ["1"]
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        # Direct content host also works: dl.dropboxusercontent.com
        return urllib.parse.urlunparse((
            parsed.scheme,
            "dl.dropboxusercontent.com",
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    # 2. Google Drive link conversion
    if "drive.google.com" in hostname:
        # Pattern 1: /file/d/{FILE_ID}/view
        m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", parsed.path)
        if m:
            file_id = m.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

        # Pattern 2: ?id={FILE_ID}
        query_params = urllib.parse.parse_qs(parsed.query)
        if "id" in query_params:
            file_id = query_params["id"][0]
            return f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

    return url
