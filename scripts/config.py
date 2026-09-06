"""
Configuration for Toutiao Publisher Skill
Centralizes constants, selectors, and paths
"""

import os
from pathlib import Path


DATA_DIR_ENV_VAR = "SUPER_PUBLISHER_DATA_DIR"


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_data_dir(value=None, home=None):
    """Resolve one agent-neutral data directory for all local installations."""
    home_dir = Path(home) if home is not None else Path.home()
    configured = value if value is not None else os.getenv(DATA_DIR_ENV_VAR)

    if configured:
        data_dir = Path(configured).expanduser()
        if not data_dir.is_absolute():
            data_dir = home_dir / data_dir
    elif home is not None:
        data_dir = home_dir / ".super-publisher" / "toutiao-publisher"
    else:
        # Default to project-local directory on D: drive to prevent C: drive pollution
        data_dir = PROJECT_ROOT / ".data"

    return data_dir


# Paths
DATA_DIR = resolve_data_dir()
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"

# URLs
LOGIN_URL = "https://mp.toutiao.com/auth/page/login"
PUBLISH_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"
HOME_URL = "https://mp.toutiao.com/"

# Browser Configuration
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",  # Patches navigator.webdriver
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--start-maximized",
    "--disable-session-crashed-bubble",
    "--hide-crash-restore-bubble",
]

# Timeouts
LOGIN_TIMEOUT_MINUTES = 10
PAGE_LOAD_TIMEOUT = 30000
DEFAULT_TIMEOUT = 30000

# Default Publishing Preferences
DEFAULT_LOCATION = "广州"

