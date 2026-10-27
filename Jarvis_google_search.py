import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@function_tool
async def google_search(query: str) -> str:
    """Performs a web search using Google Custom Search or DuckDuckGo fallback."""
    logger.info(f"🔍 Search Query: {query}")

    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    # Try Google Search API if keys are present
    if api_key and search_engine_id:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": query,
                "num": 3
            }
            logger.info("Sending request to Google Custom Search API...")
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get("items", [])
                if results:
                    formatted = ""
                    for i, item in enumerate(results, start=1):
                        title = item.get("title", "No title")
                        link = item.get("link", "No link")
                        snippet = item.get("snippet", "")
                        formatted += f"{i}. {title}\n{link}\n{snippet}\n\n"
                    return formatted.strip()
        except Exception as e:
            logger.warning(f"Google Search failed, trying DuckDuckGo fallback: {e}")

    # Fallback to DuckDuckGo search
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        logger.info("Using DuckDuckGo search fallback...")
        results = list(DDGS().text(query, max_results=3))
        if results:
            formatted = ""
            for i, item in enumerate(results, start=1):
                title = item.get("title", "No title")
                link = item.get("href", item.get("link", ""))
                snippet = item.get("body", item.get("snippet", ""))
                formatted += f"{i}. {title}\n{link}\n{snippet}\n\n"
            return formatted.strip()
        else:
            return "कोई search results नहीं मिले।"
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return f"Search processing error: {e}"

@function_tool
async def get_current_datetime() -> str:
    """Returns the current date and time formatted nicely."""
    now = datetime.now()
    return f"Current date and time: {now.strftime('%A, %B %d, %Y - %I:%M %p')}"
