"""Launch Dubai Prod Agent as a desktop chat window."""

import sys
import threading
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()


def start_server():
    """Run FastAPI server in background thread."""
    import uvicorn
    from app.server import app
    uvicorn.run(app, host="127.0.0.1", port=9999, log_level="warning")


def main():
    use_browser = "--browser" in sys.argv

    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    if use_browser:
        # Open in default browser — full copy/paste, dev tools, everything
        print("Dubai Prod Agent running at http://127.0.0.1:9999")
        print("Press Ctrl+C to stop")
        webbrowser.open("http://127.0.0.1:9999")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        # Desktop window with text selection enabled
        import webview
        window = webview.create_window(
            title="Dubai Prod Agent",
            url="http://127.0.0.1:9999",
            width=1200,
            height=800,
            resizable=True,
            confirm_close=False,
            text_select=True,
        )
        webview.start()


if __name__ == "__main__":
    main()
