import subprocess, sys, time, re, collections

HOST, PORT, GAMES = "127.0.0.1", 8000, 30


results = collections.Counter()
# 正規表現を使って、出力のパターンを検出
you_win  = re.compile(r"\byou win\b",  re.I)
you_lose = re.compile(r"\byou lose\b", re.I)
draw     = re.compile(r"\bdraw\b",     re.I)

for i in range(1, GAMES + 1):
    print(f"=== Game {i}/{GAMES} ===", file=sys.stderr)

    p1 = subprocess.Popen(
        ["python", "-u", "samples/random_player.py", HOST, str(PORT)],
        stdout=subprocess.PIPE, text=True
    )
    p2 = subprocess.Popen(
        ["python", "-u", "samples/isMinimax_player.py", HOST, str(PORT)],
        stdout=subprocess.PIPE, text=True
    )

    out1, _ = p1.communicate()   # 終局まで待機する
    out2, _ = p2.communicate()

    if you_win.search(out1):
        results["random_player win"] += 1
    elif you_win.search(out2):
        results["isMinimax_player win"] += 1
    elif draw.search(out1) or draw.search(out2):
        results["draw"] += 1
    else:
        results["unknown"] += 1     # 例外／クラッシュ検知用

print(f"\n==== {GAMES} ゲーム結果 =====")
for k, v in results.items():
    print(f"{k:24}: {v}")
