import os

def get_project_root():
    """Get absolute path to project root."""
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def get_asset_path(filename):
    """Get absolute path to an asset file."""
    return os.path.join(get_project_root(), 'assets', filename)
