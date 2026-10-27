import os
import subprocess
import sys
import logging
from fuzzywuzzy import process
from livekit.agents import function_tool
import asyncio

try:
    import pygetwindow as gw
except ImportError:
    gw = None

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow not available")
        return False

    await asyncio.sleep(1.5)
    title_keyword = title_keyword.lower().strip()

    try:
        for window in gw.getAllWindows():
            if title_keyword in window.title.lower():
                if window.isMinimized:
                    window.restore()
                window.activate()
                logger.info(f"🪟 Window focused: {window.title}")
                return True
    except Exception as e:
        logger.warning(f"⚠ Could not focus window: {e}")
    return False

async def index_files(base_dirs):
    file_index = []
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            try:
                for root, _, files in os.walk(base_dir):
                    for f in files:
                        file_index.append({
                            "name": f,
                            "path": os.path.join(root, f),
                            "type": "file"
                        })
            except Exception as e:
                logger.warning(f"Error indexing directory {base_dir}: {e}")
    logger.info(f"✅ Total {len(file_index)} files indexed.")
    return file_index

async def search_file(query, index):
    choices = [item["name"] for item in index]
    if not choices:
        logger.warning("⚠ No files available to search.")
        return None

    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' (Score: {score})")
    if score > 70:
        for item in index:
            if item["name"] == best_match:
                return item
    return None

async def open_file(item):
    try:
        logger.info(f"📂 Opening file: {item['path']}")
        if os.name == 'nt':
            os.startfile(item["path"])
        else:
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', item["path"]])
        await focus_window(item["name"])
        return f"✅ File opened: {item['name']}"
    except Exception as e:
        logger.error(f"❌ Error opening file: {e}")
        return f"❌ Failed to open file: {e}"

async def handle_command(command, index):
    item = await search_file(command, index)
    if item:
        return await open_file(item)
    else:
        logger.warning("❌ File not found.")
        return "❌ File not found."

@function_tool
async def Play_file(name: str) -> str:
    """Plays or opens a media/document file (MP4, MP3, PDF, PPT, Images, etc.) by name."""
    possible_dirs = [
        "D:/",
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Videos"),
        os.path.join(os.path.expanduser("~"), "Music"),
    ]
    folders_to_index = [d for d in possible_dirs if os.path.exists(d)]
    index = await index_files(folders_to_index)
    command = name.strip()
    return await handle_command(command, index)
