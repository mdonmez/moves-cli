import re
from pathlib import Path
from tempfile import NamedTemporaryFile

import httpx


def is_google_url(url: str) -> bool:
    """Check if URL is a Google Docs, Slides, or Drive URL."""
    patterns = [
        r"docs\.google\.com/(document|spreadsheets|presentation)",
        r"drive\.google\.com/(file|open)",
    ]
    return any(re.search(pattern, url) for pattern in patterns)


def extract_google_id(url: str) -> str | None:
    """Extract document/file ID from Google URL.

    Supports:
    - docs.google.com/document/d/{ID}/...
    - docs.google.com/presentation/d/{ID}/...
    - drive.google.com/file/d/{ID}/...
    - drive.google.com/open?id={ID}
    """
    # Pattern for /d/{ID}/ format
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)

    # Pattern for ?id={ID} format
    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)

    return None


def construct_export_url(url: str, file_id: str) -> str:
    """Construct appropriate export URL based on Google service type.

    Returns PDF export URL for all supported types.
    """
    if "docs.google.com/document" in url:
        # Google Docs -> PDF
        return f"https://docs.google.com/document/d/{file_id}/export?format=pdf"
    elif "docs.google.com/presentation" in url or "docs.google.com/presentation" in url:
        # Google Slides -> PDF
        return f"https://docs.google.com/presentation/d/{file_id}/export/pdf"
    elif "drive.google.com" in url:
        # Google Drive direct download
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    else:
        raise ValueError(f"Unsupported Google URL format: {url}")


def download_google_file(url: str) -> Path:
    """Download file from Google URL and return temporary file path.

    Args:
        url: Google Docs, Slides, or Drive URL

    Returns:
        Path to downloaded temporary file

    Raises:
        ValueError: If URL is not a valid Google URL
        RuntimeError: If download fails (network, permissions, rate limit)
    """
    if not is_google_url(url):
        raise ValueError(f"Not a Google URL: {url}")

    file_id = extract_google_id(url)
    if not file_id:
        raise ValueError(f"Could not extract file ID from URL: {url}")

    export_url = construct_export_url(url, file_id)

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(export_url)

            if response.status_code == 403:
                raise RuntimeError(
                    "Access denied (403). File may be private or sharing is disabled.\n"
                    "Make sure the file is shared as 'Anyone with the link'."
                )
            elif response.status_code == 404:
                raise RuntimeError("File not found (404). Check if the URL is correct.")
            elif response.status_code == 429:
                raise RuntimeError(
                    "Rate limit exceeded (429). Please try again in a few minutes."
                )
            elif response.status_code != 200:
                raise RuntimeError(
                    f"Download failed with status {response.status_code}: {response.text[:200]}"
                )

            # Determine file extension from Content-Type or URL
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" in content_type or "pdf" in export_url:
                suffix = ".pdf"
            elif "text" in content_type:
                suffix = ".txt"
            else:
                suffix = ".pdf"  # Default to PDF

            # Create temporary file
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(response.content)
                return Path(tmp_file.name)

    except httpx.TimeoutException:
        raise RuntimeError(
            "Download timed out after 30 seconds. Check your internet connection."
        )
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error during download: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error downloading file: {e}")


def resolve_source_path(source: str) -> Path:
    """Resolve source string to a file path.

    If source is a Google URL, downloads it and returns temp file path.
    Otherwise, treats it as a local path.

    Args:
        source: Local file path or Google URL

    Returns:
        Path to accessible file (either original local path or downloaded temp file)

    Raises:
        ValueError: If URL is invalid
        RuntimeError: If download fails
        FileNotFoundError: If local path doesn't exist
    """
    if is_google_url(source):
        return download_google_file(source)

    # Treat as local path
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {source}")

    return path.resolve()
