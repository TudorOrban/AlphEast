
from pathlib import Path
import sys
from typing import Optional


def find_project_root(marker_files=None) -> Optional[Path]:
    """
    Finds the project root by searching for marker files in parent directories.

    Args:
        marker_files (list, optional): A list of filenames or directory names
                                       to look for. Defaults to common project
                                       root markers.

    Returns:
        pathlib.Path or None: The path to the project root, or None if not found.
    """
    if marker_files is None:
        marker_files = [".git", "pyproject.toml", "setup.py", "requirements.txt", "alpheast_config.json", ".alpheast_root"]

    # Start from the directory of the file where this function is called
    current_file_dir = Path(sys.modules['__main__'].__file__).resolve().parent

    for parent in [current_file_dir] + list(current_file_dir.parents):
        for marker in marker_files:
            if (parent / marker).exists() or (parent / marker).is_dir():
                return parent
    return None