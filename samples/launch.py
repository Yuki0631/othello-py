import subprocess
import webbrowser
import time
import os


# 1. サーバ（FastAPI）を起動
server_proc = subprocess.Popen(["uvicorn", "samples.server:app", "--reload"])

# 2. 少し待機してから manual_player_ws と random_player_ws を起動
time.sleep(1)
manual_proc = subprocess.Popen(["python", "samples/manual_player_ws.py", "localhost", "8000"])
time.sleep(1)
random_proc = subprocess.Popen(["python", "samples/random_player_ws.py", "localhost", "8000"])

# 3. index.html をブラウザで開く（絶対パスに変更）
#html_path = os.path.abspath("webUI/index.html")  # webUIフォルダの中を指定
webbrowser.open("http://localhost:8000/")


# 4. プロセスが終わるまで待機
try:
    server_proc.wait()
except KeyboardInterrupt:
    print("Shutting down...")
    server_proc.terminate()
    manual_proc.terminate()
    random_proc.terminate()
