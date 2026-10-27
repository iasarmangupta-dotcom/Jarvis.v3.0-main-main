from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)
from Jarvis_prompts import behavior_prompts, Reply_prompts
from Jarvis_google_search import google_search, get_current_datetime
from jarvis_get_whether import get_weather
from Jarvis_window_CTRL import open, open_website, close, folder_file, system_control, take_screenshot
from Jarvis_file_opner import Play_file
from keyboard_mouse_CTRL import (
    move_cursor_tool,
    mouse_click_tool,
    scroll_cursor_tool,
    type_text_tool,
    press_key_tool,
    swipe_gesture_tool,
    press_hotkey_tool,
    control_volume_tool
)

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=behavior_prompts,
            tools=[
                google_search,
                get_current_datetime,
                get_weather,
                open,                # Apps / Websites launch karne ke liye
                open_website,        # Direct URLs open karne ke liye
                close,               # Windows close karne ke liye
                folder_file,         # Folder / File operations (create, rename, delete, open)
                Play_file,           # MP4, MP3, PDF, PPT, Images open/play karne ke liye
                system_control,      # System lock, shutdown, restart, sleep karne ke liye
                take_screenshot,     # Screen capture lene ke liye
                move_cursor_tool,    # Mouse move karne ke liye
                mouse_click_tool,    # Mouse click karne ke liye
                scroll_cursor_tool,  # Scroll karne ke liye
                type_text_tool,      # Typing karne ke liye
                press_key_tool,      # Single key press karne ke liye
                press_hotkey_tool,   # Shortcut keys press karne ke liye (e.g., ctrl+c, alt+tab)
                control_volume_tool, # Volume control karne ke liye
                swipe_gesture_tool   # Swipe gestures ke liye
            ]
        )


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon"
        )
    )
    
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            video_enabled=True 
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=Reply_prompts
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
