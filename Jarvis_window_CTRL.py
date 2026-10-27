import os
import subprocess
import logging
import sys
import asyncio
import webbrowser
import ctypes
import pyautogui
from datetime import datetime
from fuzzywuzzy import process

try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func): 
        return func

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Extended App command map
APP_MAPPINGS = {
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "browser": "chrome",
    "vlc": "vlc",
    "command prompt": "cmd",
    "cmd": "cmd",
    "terminal": "wt",
    "powershell": "powershell",
    "control panel": "control",
    "settings": "start ms-settings:",
    "paint": "mspaint",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "postman": "postman",
    "task manager": "taskmgr",
    "explorer": "explorer",
    "this pc": "explorer",
    "my computer": "explorer",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "spotify": "spotify",
    "whatsapp": "whatsapp"
}

# Popular websites dictionary
WEBSITE_MAPPINGS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "whatsapp web": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com"
}

# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow not available")
        return False

    await asyncio.sleep(1.5)  # Give time for window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                for d in dirs:
                    item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
                for f in files:
                    item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"✅ Indexed {len(item_index)} items.")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया। {e}")

async def play_file(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ फ़ाइल open करने में error आया।: {e}")

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder create हो गया: {path}"
    except Exception as e:
        return f"❌ Folder create करने में error आया: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ नाम बदलकर {new_path} कर दिया गया।"
    except Exception as e:
        return f"❌ नाम बदलना fail हो गया: {e}"

async def delete_item(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ Deleted: {path}"
    except Exception as e:
        return f"❌ Delete नहीं हुआ: {e}"

# -------------------------
# LiveKit Tools
# -------------------------

@function_tool
async def open(app_title: str) -> str:
    """Opens an application on the PC or a popular website."""
    app_key = app_title.lower().strip()

    # Check if it's a known website first
    if app_key in WEBSITE_MAPPINGS:
        url = WEBSITE_MAPPINGS[app_key]
        webbrowser.open(url)
        return f"🚀 Opening website: {url}"

    # Check if user passed a URL directly
    if app_key.startswith("http://") or app_key.startswith("https://") or app_key.endswith(".com") or app_key.endswith(".in") or app_key.endswith(".org"):
        url = app_key if app_key.startswith("http") else f"https://{app_key}"
        webbrowser.open(url)
        return f"🚀 Opening website: {url}"

    app_command = APP_MAPPINGS.get(app_key, app_key)
    try:
        await asyncio.create_subprocess_shell(f'start "" "{app_command}"', shell=True)
        focused = await focus_window(app_title)
        if focused:
            return f"🚀 App launch हुआ और focus में है: {app_title}."
        else:
            return f"🚀 {app_title} launch किया गया।"
    except Exception as e:
        return f"❌ {app_title} launch नहीं हो पाया: {e}"

@function_tool
async def open_website(url: str) -> str:
    """Opens any website URL or site name in the browser."""
    clean_url = url.lower().strip()
    target_url = WEBSITE_MAPPINGS.get(clean_url, clean_url)
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = f"https://{target_url}"
    webbrowser.open(target_url)
    return f"🌐 Opening website: {target_url}"

@function_tool
async def close(window_title: str) -> str:
    """Closes an open window or application by title."""
    if not win32gui:
        return "❌ win32gui not available."

    closed_any = False
    def enumHandler(hwnd, _):
        nonlocal closed_any
        if win32gui.IsWindowVisible(hwnd):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed_any = True

    win32gui.EnumWindows(enumHandler, None)
    if closed_any:
        return f"✅ Window closed: {window_title}"
    else:
        return f"⚠️ No visible window matching '{window_title}' found."

@function_tool
async def folder_file(command: str) -> str:
    """Creates, renames, deletes or opens folders and files on the system."""
    folders_to_index = ["D:/", "C:/Users"]
    index = await index_items(folders_to_index)
    command_lower = command.lower()

    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ Rename command format valid नहीं है (e.g. rename old_name to new_name)."

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ Delete करने के लिए item नहीं मिला।"

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"✅ Folder opened: {item['name']}"
        return "❌ Folder नहीं मिला।"

    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"✅ File opened: {item['name']}"

    return "⚠ File या Folder match नहीं हुआ।"

@function_tool
async def system_control(action: str) -> str:
    """Controls system power actions: lock, shutdown, restart, sleep."""
    act = action.lower().strip()
    try:
        if act in ["lock", "lock pc", "lock computer"]:
            ctypes.windll.user32.LockWorkStation()
            return "🔒 Computer lock कर दिया गया है।"
        elif act in ["shutdown", "turn off"]:
            os.system("shutdown /s /t 10")
            return "🛑 Computer 10 seconds में shutdown हो जाएगा।"
        elif act in ["restart", "reboot"]:
            os.system("shutdown /r /t 10")
            return "🔄 Computer 10 seconds में restart हो जाएगा।"
        elif act in ["sleep"]:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "🌙 Computer sleep mode में जा रहा है।"
        else:
            return f"⚠️ Unknown system action: {action}. Supported: lock, shutdown, restart, sleep."
    except Exception as e:
        return f"❌ System action fail हो गया: {e}"

@function_tool
async def take_screenshot() -> str:
    """Takes a screenshot of the current screen and saves it."""
    try:
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Jarvis_Screenshots")
        os.makedirs(pictures_dir, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(pictures_dir, filename)
        pyautogui.screenshot(filepath)
        return f"📸 Screenshot captured and saved to: {filepath}"
    except Exception as e:
        return f"❌ Screenshot लेने में error आया: {e}"
