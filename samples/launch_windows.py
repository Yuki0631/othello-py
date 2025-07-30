import subprocess
import webbrowser
import time
import os


# 1. サーバ（FastAPI）を起動 (WindowsOS)
server_proc = subprocess.Popen(["-m", "uvicorn", "samples.server:app", "--reload"])

# 2. 少し待機してから manual_player_ws と random_player_ws を起動
time.sleep(1)
manual_proc = subprocess.Popen(["python", "samples/manual_player_ws.py", "localhost", "8000"])
time.sleep(1)
random_proc = subprocess.Popen(["python", "samples/random_player_ws.py", "localhost", "8000"])
#isMinimax_proc = subprocess.Popen(["python", "samples/isMinimax_player.py", "localhost", "8000"])

# 3. index.html をブラウザで開く
webbrowser.open("http://localhost:8000/")


# 4. プロセスが終わるまで待機
try:
    server_proc.wait()
except KeyboardInterrupt:
    print("Shutting down...")
    server_proc.terminate()
    manual_proc.terminate()
    random_proc.terminate()
    #isMinimax_proc.terminate()
