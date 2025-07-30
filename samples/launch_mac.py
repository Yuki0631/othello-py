import subprocess
import webbrowser
import time
import os


# 1. サーバ（FastAPI）を起動 (MacOS)
server_proc = subprocess.Popen(["uvicorn", "samples.server:app", "--reload"])

# 2. 少し待機してからAI player を起動
# random か isMinimax かを選択する

time.sleep(1)
player_value = input("choose random player -> 0 / minimax player -> 1 : ")


try:
    player_choice = int(player_value) 

    if player_choice == 0:
        print("Activating random player...")
        random_proc = subprocess.Popen(["python", "samples/random_player_ws.py", "localhost", "8000"])
    elif player_choice == 1:
        print("Activating minimax player...")
        isMinimax_proc = subprocess.Popen(["python", "samples/isMinimax_player_ws.py", "localhost", "8000"])
except ValueError:
    print("!Invalid value error!")

time.sleep(1)

# 3. index.html をブラウザで開く
webbrowser.open("http://localhost:8000/")

# 4. プロセスが終わるまで待機
try:
    server_proc.wait()
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    # 各プロセスが起動していれば終了させる
    if server_proc.poll() is None: # サーバーがまだ実行中なら
        server_proc.terminate()
        server_proc.wait(timeout=5) # 終了を待つ

    if random_proc and random_proc.poll() is None:
        random_proc.terminate()
        random_proc.wait(timeout=5)

    if isMinimax_proc and isMinimax_proc.poll() is None:
        isMinimax_proc.terminate()
        isMinimax_proc.wait(timeout=5)
    print("All of the processes finally closed. Thank you for playing!")
