import os
import importlib
import sys
from urllib.request import urlopen
from urllib.parse import urlparse
from shared.logger import setup_logger

logger = setup_logger("plugin_downloader")

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), '../plugins')
PLUGINS_DIR = os.path.abspath(PLUGINS_DIR)


def download_and_load_plugin(plugin_url: str) -> str:
    """
    Download a plugin Python file from a URL, save it to the plugins directory, and load it as a module.
    The filename is derived from the URL.
    """
    parsed = urlparse(plugin_url)
    filename = os.path.basename(parsed.path)
    if not filename.endswith('.py'):
        return "Plugin URL must end with .py"
    plugin_name = filename[:-3]
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR)
    plugin_path = os.path.join(PLUGINS_DIR, filename)
    try:
        with urlopen(plugin_url) as resp:
            code = resp.read().decode('utf-8')
        with open(plugin_path, 'w', encoding='utf-8') as f:
            f.write(code)
        logger.info(f"Downloaded plugin {plugin_name} from {plugin_url}")
        # Try to load the plugin
        module_name = f"logic_server.plugins.{plugin_name}"
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
        return f"Plugin {plugin_name} downloaded and loaded."
    except Exception as e:
        logger.error(f"Failed to download/load plugin: {e}")
        return f"Failed to download/load plugin: {e}"
