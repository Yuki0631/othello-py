from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import subprocess
import os
import json
from src.othello_py.field import OthelloField
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse



app = FastAPI()
app.mount("/static", StaticFiles(directory="webUI", html=True), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

# CORS許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocketのグローバル変数
player_connection = None
ui_connection = None

@app.websocket("/ws/player")
async def websocket_player(ws: WebSocket):
    global player_connection
    await ws.accept()
    player_connection = ws
    print("player connected")

    try:
        while True:
            data = await ws.receive_text()
            if ui_connection:
                await ui_connection.send_text(data)
    except:
        print("player disconnected")

@app.websocket("/ws/ui")
async def websocket_ui(ws: WebSocket):
    global ui_connection
    await ws.accept()
    ui_connection = ws
    print("UI connected")

    try:
        while True:
            data = await ws.receive_text()
            if player_connection:
                await player_connection.send_text(data)
    except:
        print("UI disconnected")

@app.websocket("/ws/board")
async def websocket_endpoint(ws: WebSocket):
    print("⚡ WebSocket /ws/board handler called")
    await ws.accept()
    from othello_py.field import OthelloField

    field = OthelloField()
    # boardを0,1,Noneの2次元リストに変換
    board_data = [[
        cell.owner if cell is not None else None
        for cell in row
    ] for row in field.board]
    
    data = {
        "type": "initial_board",
        "board": board_data
    }
    print("Initial board_data:", board_data)  # ログに初期盤面を表示
    await ws.send_text(json.dumps(data))

    # 以降は受信待ちや処理を書いてもよいが、今回は初期盤面のみ送信して終了
    await ws.close()
