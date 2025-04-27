# Configuration for PythonLolo IRC Bot

import os
import json

# Base directory and config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
try:
    with open(CONFIG_FILE) as f:
        _conf = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    _conf = {}

# Bot settings
BOT_NICK = _conf['BOT_NICK']
IRC_SERVER = _conf['IRC_SERVER']
IRC_PORT = _conf['IRC_PORT']
IRC_CHANNEL = _conf['IRC_CHANNEL']
IRC_AUTOCHANNELS = _conf['IRC_AUTOCHANNELS']

# Logic server WebSocket settings
LOGIC_SERVER_HOST = _conf['LOGIC_SERVER_HOST']
LOGIC_SERVER_PORT = _conf['LOGIC_SERVER_PORT']

# Database settings
DATABASE_FILE = _conf['DATABASE_FILE']
DB_PATH = os.path.join(BASE_DIR, DATABASE_FILE)

def save_config():
    """Save modifications back to config.json."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(_conf, f, indent=2)
