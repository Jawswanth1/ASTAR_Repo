"""Open the chapter-one demo, reusing a matching ASTAR server when available."""
from pathlib import Path
import json
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

root=Path(__file__).resolve().parents[1]
port=8792
url=f'http://127.0.0.1:{port}'
try:
    with urllib.request.urlopen(url+'/api/demos',timeout=2) as response:
        data=json.loads(response.read())
        if not isinstance(data,list):raise ValueError('Unexpected service')
    webbrowser.open(url+'/demo/')
    print('Opened the existing Chapter One Lab server.')
    sys.exit(0)
except (OSError,ValueError):
    pass
with socket.socket() as probe:
    if probe.connect_ex(('127.0.0.1',port))==0:
        print('Port 8792 is already in use by another service. Choose another port with python -m astar_app.server --port 8793, then open /demo/.')
        sys.exit(1)
process=subprocess.Popen([sys.executable,'-m','astar_app.server','--port',str(port)],cwd=root)
try:
    for _ in range(80):
        if process.poll() is not None:raise RuntimeError('Server did not start. Run setup.bat to install dependencies.')
        try:
            with urllib.request.urlopen(url+'/api/demos',timeout=2) as response:
                if response.status==200:break
        except OSError:time.sleep(.25)
    else:raise RuntimeError('The local server did not become ready.')
    webbrowser.open(url+'/demo/')
    print('Keep this window open. Press Ctrl+C to stop the demo.')
    process.wait()
except KeyboardInterrupt:
    pass
finally:
    if process.poll() is None:process.terminate()
