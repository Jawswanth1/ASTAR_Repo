"""Start the current Chapter 1 app and open its clean entry screen."""
from pathlib import Path
import subprocess,sys,time,urllib.request,webbrowser
ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8790/'

def ready():
    try:
        with urllib.request.urlopen(URL,timeout=2) as response:
            return b'/learn/app.js' in response.read()
    except OSError:return False

if ready():webbrowser.open(URL)
else:
    process=subprocess.Popen([sys.executable,'-m','astar_app.server','--port','8790'],cwd=ROOT)
    try:
        for _ in range(60):
            if process.poll() is not None:raise RuntimeError('ASTAR did not start. Run setup.bat and check that port 8790 is available.')
            if ready():break
            time.sleep(.25)
        else:raise RuntimeError('ASTAR did not become ready.')
        webbrowser.open(URL)
        print('ASTAR is ready. Keep this window open; Ctrl+C closes the local app.')
        process.wait()
    except KeyboardInterrupt:pass
    finally:
        if process.poll() is None:process.terminate()
