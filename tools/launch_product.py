"""Open the 3D explorer, reusing only a compatible local ASTAR instance."""
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
PORT = 8783
URL = f"http://127.0.0.1:{PORT}/product/"


def ready():
    try:
        with urllib.request.urlopen(URL, timeout=2) as response:
            return response.status == 200 and b"ASTAR" in response.read(4096) and response.headers.get_content_type() == "text/html"
    except OSError:
        return False


if ready():
    webbrowser.open(URL)
    print(f"Opened the existing ASTAR explorer: {URL}")
else:
    process = subprocess.Popen([sys.executable, "-m", "astar_app.server", "--port", str(PORT)], cwd=ROOT)
    try:
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError("The server could not start. Check that port 8783 is free and run setup.bat if dependencies are missing.")
            if ready():
                break
            time.sleep(.25)
        else:
            raise RuntimeError("The local explorer did not become ready.")
        webbrowser.open(URL)
        print("Keep this window open for the 3D explorer. Press Ctrl+C to stop.")
        process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if process.poll() is None:
            process.terminate()
