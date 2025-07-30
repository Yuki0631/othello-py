"""
import socket
import logging
from .field import OthelloField
from .protocol import Command, serialize_board, parse_move, Protocol
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import argparse, logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import threading

# --- FastAPI WebSocketサーバの実装 ---

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

player_ws = None  # manual_player_ws用WebSocket接続
ui_ws = None      # UI用WebSocket接続

@app.websocket("/ws/player")
async def websocket_player(ws: WebSocket):
    global player_ws
    await ws.accept()
    player_ws = ws
    print("player WS connected")
    try:
        while True:
            data = await ws.receive_text()
            if ui_ws:
                await ui_ws.send_text(data)  # UIへ中継
    except WebSocketDisconnect:
        print("player WS disconnected")
        player_ws = None

@app.websocket("/ws/ui")
async def websocket_ui(ws: WebSocket):
    global ui_ws
    await ws.accept()
    ui_ws = ws
    print("UI WS connected")
    try:
        while True:
            data = await ws.receive_text()
            if player_ws:
                await player_ws.send_text(data)  # playerへ中継
    except WebSocketDisconnect:
        print("UI WS disconnected")
        ui_ws = None

MAX_ILLEGAL = 1000 # 不正手の最大カウント

def handle_game(clients, quiet=False):
    '''
    ゲームのメインループを処理する関数
    clients: クライアントのファイルオブジェクトのリスト
    quiet: Trueならサーバ側のログを抑制する
    '''
    field = OthelloField() # Othelloの盤面を初期化
    illegal_counts = [0, 0] # 不正手のカウント
    turn = 0 # ターン数
    passes = [0, 0] # パスのカウント

    # 初期送信：ID, 挨拶, 初期盤面
    for pid, cl in enumerate(clients): # pidはプレイヤーID, clはクライアントのファイルオブジェクト
        print(f"{Command.ID.value} {pid}", file=cl) # プレイヤーIDを送信
        print(Protocol.greeting, file=cl) # 挨拶を送信
        print(serialize_board(field.get_visible_board(pid)), file=cl) # 初期盤面を送信

    while True:
        curr = turn % 2 # 現在のプレイヤーID（0または1), 2で割った余りを使う
        opp  = 1 - curr # 相手のプレイヤーID（0または1）
        active, passive = clients[curr], clients[opp] # アクティブなプレイヤーとパッシブなプレイヤーのファイルオブジェクト

        # サーバ側コンソール表示
        logging.info(f"--- Turn {turn} ---")
        logging.info(f"Illegal counts → P0: {illegal_counts[0]}, P1: {illegal_counts[1]}")
        for y in range(field.SIZE): # 盤面の行をループ
            # 各行の文字列を生成
            row = ''.join(
                '.' if field.board[y][x] is None
                else ('○' if field.board[y][x].owner == 0 else '●')
                for x in range(field.SIZE)
            )
            logging.info(row)

        # ターン通知
        print("your turn", file=active) # アクティブなプレイヤーにターン通知
        print("waiting",   file=passive) # パッシブなプレイヤーに待機通知

        line = active.readline().strip() # アクティブなプレイヤーからの入力を読み込む

        if not line: # 入力が空なら接続が切れたと判断
            logging.error("Client disconnected")
            break

        if line == Command.PASSED.value: # パスの場合
            passes[curr] += 1 # パスのカウントを増やす
            flips = 0 # パスの場合はひっくり返る石の数は0
        else: # 着手の場合
            try:
                x, y = parse_move(line)
                flips = field.place(x, y, curr) # 着手を盤面に反映し、ひっくり返る石の数を取得
                passes[curr] = 0 # パスのカウントをリセット
            except ValueError:
                illegal_counts[curr] += 1 # 不正手カウントを増やす
                if illegal_counts[curr] >= MAX_ILLEGAL:
                    print(Protocol.you_lose, file=active) # 不正手が最大値に達した場合、負けを通知
                    print(Protocol.you_win,  file=passive) # 相手には勝ちを通知
                    return
                # 不正手通知
                print(f"{Command.ILLEGAL_COUNT.value} {illegal_counts[curr]} {illegal_counts[opp]}", file=active)
                # 再打ち盤面を見せる
                print(serialize_board(field.get_visible_board(curr)), file=active)
                continue

        # 正常手レスポンス
        for cl in clients:
            print(f"{Command.FLIP_COUNT.value} {flips}", file=cl)
        print(serialize_board(field.get_visible_board(curr)), file=active)
        print(serialize_board(field.get_visible_board(opp)),  file=passive)

        # 終了判定
        no_moves = not field.legal_moves(0) and not field.legal_moves(1) # 両プレイヤーが合法手なしの場合
        if (passes[0] > 1 and passes[1] > 1) or no_moves: # 両プレイヤーが連続でパスした場合、または合法手がない場合
            counts = [0,0] # 石のカウントを初期化
            for row in field.board:
                for p in row:
                    if p: counts[p.owner]+=1 # 石の所有者ごとにカウント
            diff = counts[0] - counts[1] # 差分を計算
            for pid, cl in enumerate(clients): # 各プレイヤーに結果を通知
                if diff==0:      outcome = Protocol.draw 
                elif (diff>0 and pid==0) or (diff<0 and pid==1): outcome = Protocol.you_win
                else:          outcome = Protocol.you_lose
                print(outcome, file=cl)
            return

        turn += 1

def server_main(host: str, port: int, games: int = 1, *, quiet=False):
    with socket.create_server((host, port)) as srv:
        for _ in range(games):
            logging.info(f"Waiting for players at {host}:{port}")
            clients = []
            for i in range(2):
                conn, addr = srv.accept()
                cl = conn.makefile(mode='rw', buffering=1, encoding='utf-8')
                logging.info(f"Player {i+1} connected from {addr}")
                clients.append(cl)
            handle_game(clients, quiet=quiet)
            for cl in clients:
                cl.close()

# --- サーバ起動部分の切り分け ---

def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--games", type=int, default=1)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--mode", choices=["tcp", "ws"], default="tcp", help="tcp=既存TCPサーバ, ws=FastAPI起動")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    if args.mode == "tcp":
        # 既存TCPソケットサーバを起動
        server_main(args.host, args.port, args.games, quiet=args.quiet)
    else:
        # FastAPIを起動（uvicornなどから起動想定）
        import uvicorn
        uvicorn.run("src.othello_py.server:app", host=args.host, port=args.port, reload=True)

if __name__ == "__main__":
    main()
"""