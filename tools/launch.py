"""Start the local app and open the browser once it is ready."""
from pathlib import Path
import subprocess,sys,time,urllib.request,webbrowser,socket
root=Path(__file__).resolve().parents[1]
port=8780
with socket.socket() as probe:
    if probe.connect_ex(('127.0.0.1',port))==0:
        print('Port 8780 is already in use. If ASTAR is open, use its existing window. Otherwise close that server before starting ASTAR.')
        sys.exit(1)
process=subprocess.Popen([sys.executable,'-m','astar_app.server','--port',str(port)],cwd=root)
try:
    for _ in range(60):
        if process.poll() is not None:raise RuntimeError('Server did not start. Run setup.bat if dependencies are missing.')
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/',timeout=5) as response:
                response.read()
                if response.status==200:break
        except OSError:time.sleep(.25)
    else:raise RuntimeError('The local server did not become ready.')
    webbrowser.open(f'http://127.0.0.1:{port}')
    print('Keep this window open while preparing books. Press Ctrl+C to stop.')
    process.wait()
except KeyboardInterrupt:pass
finally:
    if process.poll() is None:process.terminate()
