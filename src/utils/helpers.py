import os
import re
import sys
import subprocess
from pathlib import Path

def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """Sanitize a string for use as a filename."""
    # Remove characters not allowed in filenames
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Remove leading/trailing whitespace and truncate
    return filename.strip()[:max_length]

def open_directory(path: str):
    """Open a directory in the default system file explorer."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return
        
    try:
        if os.name == "nt":  # Windows
            os.startfile(path)
        elif sys.platform == "darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass

def get_asset_path(filename: str) -> str:
    """Get the absolute path to an asset file."""
    base_dir = Path(__file__).parent.parent.parent
    asset_path = base_dir / "assets" / filename
    return str(asset_path)
