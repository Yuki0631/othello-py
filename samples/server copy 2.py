import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi.staticfiles import StaticFiles
from othello_py.field import OthelloField
from fastapi.responses import RedirectResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="webUI", html=True), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

player_connection = None
ui_connection = None


# 盤面と状態をグローバルで管理
field = OthelloField()
current_player = 0  # 0=黒, 1=白

@app.websocket("/ws/player")
async def websocket_player(ws: WebSocket):
    global player_connection, field, current_player, ui_connection
    await ws.accept()
    player_connection = ws
    print("player connected")

    # サーバからプレイヤーへIDを送信（例えばcurrent_playerを文字列で送る）
    await ws.send_text(f"ID {current_player}")

    try:
        while True:
            data = await ws.receive_text()
            print(f"Received from player: {data}")

            # MOVE処理はそのまま
            if data.startswith("MOVE"):
                _, xs, ys = data.split()
                x, y = int(xs), int(ys)
                try:
                    field.place(x, y, current_player)
                    current_player = 1 - current_player

                    if ui_connection:
                        board_data = {
                            "type": "update",
                            "board": field.get_board_state(),
                            "legal_moves": [list(m) for m in field.legal_moves(current_player)],
                            "current_player": current_player
                        }
                        await ui_connection.send_text(json.dumps(board_data))

                    board_data = {
                        "type": "update",
                        "board": field.get_board_state(),
                        "legal_moves": [list(m) for m in field.legal_moves(current_player)],
                        "current_player": current_player
                    }
                    await ws.send_text(json.dumps(board_data))

                except ValueError:
                    await ws.send_text(json.dumps({"type": "error", "message": "Illegal move"}))
    except WebSocketDisconnect:
        print("player disconnected")
        player_connection = None



@app.websocket("/ws/ui")
async def websocket_ui(ws: WebSocket):
    global ui_connection
    await ws.accept()
    ui_connection = ws
    print("UI connected")

    try:
        while True:
            data = await ws.receive_text()
            # UIからのメッセージをplayerに転送（必要なら）
            if player_connection:
                await player_connection.send_text(data)
    except WebSocketDisconnect:
        print("UI disconnected")
        ui_connection = None



async def send_board_state(ws: WebSocket, field: OthelloField, current_player: int):
    board_data = {
        "type": "update",
        "board": field.get_board_state(),
        "legal_moves": [list(m) for m in field.legal_moves(current_player)]
    }
    await ws.send_text(json.dumps(board_data))
'''
@app.websocket("/ws/board")
async def websocket_board(ws: WebSocket):
    await ws.accept()
    global field, current_player
    try:
        # 初回接続時に盤面情報を送信
        board_data = {
            "type": "update",
            "board": field.get_board_state(),
            "legal_moves": [list(m) for m in field.legal_moves(current_player)],
            "current_player": current_player
        }
        await ws.send_text(json.dumps(board_data))

        # 基本的にここでは受信を待たず、盤面更新は他のWSから行う運用でよい
        while True:
            data = await ws.receive_text()
            # 必要に応じてUIからの操作も受け取れるが基本は受信しなくて良い
            # ここは必要に応じて実装してください
    except WebSocketDisconnect:
        print("Board WS disconnected")
'''

@app.websocket("/ws/board")
async def websocket_board(ws: WebSocket):
    await ws.accept()
    global field, current_player, player_connection, ui_connection
    print("Board WS connected")
    try:
        # 初期盤面送信
        board_data = {
            "type": "update",
            "board": field.get_board_state(),
            "legal_moves": [list(m) for m in field.legal_moves(current_player)],
            "current_player": current_player
        }
        await ws.send_text(json.dumps(board_data))
        print("Sent initial board")

        while True:
            data = await ws.receive_text()
            print(f"Received from board WS: {data}")

            if data.startswith("MOVE"):
                _, xs, ys = data.split()
                x, y = int(xs), int(ys)
                print(f"Attempt move at ({x},{y}) by player {current_player}")

                try:
                    field.place(x, y, current_player)
                    current_player = 1 - current_player
                    print(f"Move accepted. Next player: {current_player}")

                    board_data = {
                        "type": "update",
                        "board": field.get_board_state(),
                        "legal_moves": [list(m) for m in field.legal_moves(current_player)],
                        "current_player": current_player
                    }
                    await ws.send_text(json.dumps(board_data))
                    print("Sent updated board to board WS")

                    # 【ここに追加】自動手番のプレイヤー（例：player_connection）に手番通知を送る
                    if player_connection and current_player == 1:
                        try:
                            await player_connection.send_text(json.dumps({
                                "type": "your_turn",
                                "board": field.get_board_state(),
                                "legal_moves": [list(m) for m in field.legal_moves(current_player)],
                                "current_player": current_player
                            }))
                            print("Sent board and turn info to random player")
                        except Exception as e:
                            print("Failed to send turn info to random player:", e)

                    # UIへも送る
                    if ui_connection:
                        await ui_connection.send_text(json.dumps(board_data))
                        print("Sent updated board to UI")

                    # player_connectionがいるなら何か送信など処理をここで

                except ValueError as e:
                    print(f"Illegal move: {e}")
                    await ws.send_text(json.dumps({"type": "error", "message": "Illegal move"}))

    except Exception as e:
        print(f"Exception in board WS: {e}")
    finally:
        print("Board WS disconnected")
