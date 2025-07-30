import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from othello_py.field import OthelloField

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

# グローバル状態
field = OthelloField()
current_player = 0  # 0: manual, 1: random
player_connection = None
ui_connection = None

illegal_counts = [0, 0]

#追加
def flatten_board(board):
    flat = ""
    for row in board:
        for cell in row:
            if cell is None:
                flat += "."
            else:
                flat += str(cell.owner)
    return flat

async def send_illegal_count_to_ui():
    if ui_connection:
        msg = f"ILLEGAL_COUNT {illegal_counts[0]} {illegal_counts[1]}"
        await ui_connection.send_text(msg)
        print(f"send ILLEGAL COUNT to UI: {msg}")

@app.websocket("/ws/player")
async def websocket_player(ws: WebSocket):
    global player_connection, current_player

    await ws.accept()
    player_connection = ws
    print("player connected")

    # 初期ID送信
    await ws.send_text("ID 1")
    await ws.send_text("Hello, AI player!")

    try:
        while True:
            data = await ws.receive_text()
            print("Received from player WS:", data)

            if data.startswith("MOVE"):
                _, xs, ys = data.split()
                x, y = int(xs), int(ys)
                print(f"→ Received MOVE from random player: {x},{y}")
                try:
                    field.place(x, y, current_player)
                except ValueError: #ここでエラー発生
                    print(f"Invalid move from player: {x},{y} (ValueError)") # ログをより詳細に
                    # AI (IsMinimaxPlayer) が不正手を打ったのでカウントを増やす
                    # current_player はこの時点ではまだ AI (ID 1)
                    illegal_counts[current_player] += 1
                    await send_illegal_count_to_ui() # UIに更新を通知

                    # AIに現在の盤面と合法手、そして「あなたのターン」を再送して再試行させる
                    await ws.send_text("BOARD " + flatten_board(field.board))
                    legal_moves_str = "LEGAL_MOVES " + " ".join(f"{lx},{ly}" for lx, ly in field.legal_moves(current_player))
                    await ws.send_text(legal_moves_str)
                    await ws.send_text("FLIP_COUNT 0") # フリップ数は0
                    await ws.send_text("your turn")
                    print("The board state, legal moves, and turn information have been resent to the AI (the server determined that the MOVE was invalid).")
                    continue # 不正手だったので、手番は変わらず次のAIの試行を待つ

            elif data.startswith("ILLEGAL"):
                print("→ Illegal move received from UI")
                illegal_counts[current_player] += 1
                await send_illegal_count_to_ui()
                await ws.send_text("BOARD " + flatten_board(field.board))
                legal_moves_str = "LEGAL_MOVES " + " ".join(f"{x},{y}" for x, y in field.legal_moves(current_player))
                await ws.send_text(legal_moves_str)
                await ws.send_text("FLIP_COUNT 0") # フリップ数は関係ないので0
                await ws.send_text("your turn")
                continue

            elif data == "PASSED":
                print("→ Received PASSED from player")
                # 何も置かずに手番だけ交代
                pass

            else:
                print("Unknown message:", data)
                continue

            # 手番を交代
            current_player = 1 - current_player

            # 現在の手番の合法手を取得
            legal_now = list(field.legal_moves(current_player))
            legal_opponent = list(field.legal_moves(1 - current_player))

            # 全体更新（合法手は現手番用）
            board_data = {
                "type": "update",
                "board": field.get_board_state(),
                "legal_moves": [list(m) for m in legal_now]
            }
            await board_ws.send_text(json.dumps(board_data))
            if ui_connection:
                await ui_connection.send_text(json.dumps(board_data))

            # 終了判定（両者合法手なし）
            if not legal_now and not legal_opponent:
                black = field.count_pieces(0)
                white = field.count_pieces(1)
                if black > white:
                    result_msg = f"あなたの勝ち（{black} 対 {white}）"
                elif white > black:
                    result_msg = f"AIの勝ち（{white} 対 {black}）"
                else:
                    result_msg = f"引き分け（{black} 対 {white}）"

                print(f"Game over: {result_msg}")

                # 勝敗メッセージも送信
                result_data = {
                    "type": "game_over",
                    "message": result_msg
                }
                if ui_connection:
                    await ui_connection.send_text(json.dumps(result_data))

    except WebSocketDisconnect:
        print("Player disconnected (WebSocketDisconnect)")
    except Exception as e:
        print("player disconnected", e)
    finally:
        player_connection = None




@app.websocket("/ws/ui")
async def websocket_ui(ws: WebSocket):
    global ui_connection
    await ws.accept()
    ui_connection = ws
    print("UI connected")
    
    # UI接続時に現在の不正手カウントを送信
    initial_illegal_msg = f"ILLEGAL_COUNT {illegal_counts[0]} {illegal_counts[1]}"
    await ui_connection.send_text(initial_illegal_msg)
    print("Sent initial ILLEGAL_COUNT to UI:", initial_illegal_msg)

    try:
        while True:
            data = await ws.receive_text() #ws/uiもws/boardと同時にmsg受信
            print("Received from UI WS:", data)
    except Exception as e:
        print("UI disconnected", e)


@app.websocket("/ws/board")
async def websocket_board(ws: WebSocket):
    global board_ws, current_player
    board_ws = ws
    await ws.accept()
    print("connection open")

    try:
        # 初期盤面送信
        board_data = {
            "type": "update",
            "board": field.get_board_state(),
            "legal_moves": [list(m) for m in field.legal_moves(current_player)]
        }
        await ws.send_text(json.dumps(board_data))

        while True:
            msg = await ws.receive_text()
            print("Received from board WS:", msg) #まず盤面からmsg受け取る

            if msg.startswith("ILLEGAL"):
                _, xs, ys = msg.split()
                x, y = int(xs), int(ys)
                print(f"Illegal move at ({x},{y}) reported by player {current_player}")

                illegal_counts[current_player] += 1 #ここで更新してみる

                # UI に送信
                if ui_connection:
                    msg = f"ILLEGAL_COUNT {illegal_counts[0]} {illegal_counts[1]}"
                    await ui_connection.send_text(msg)

            elif msg.startswith("MOVE"):
                _, xs, ys = msg.split()
                x, y = int(xs), int(ys)
                
                #追加
                if current_player != 0:
                    print("Ignored MOVE: Not player's turn")
                    await ws.send_text(json.dumps({"type": "error", "message": "Not your turn"}))
                    continue
        
                print(f"Attempt move at ({x},{y}) by player {current_player}") #合法なので動かします
                
                try:
                    # ここで human_player_move の結果としてフリップ数を取得
                    flips_in_human_move = field.place(x, y, current_player)
                    current_player = 1 - current_player #player変更

                    update = {
                        "type": "update",
                        "board": field.get_board_state(),
                        "legal_moves": [list(m) for m in field.legal_moves(current_player)]
                    }

                    # 盤面・UIに送信
                    await ws.send_text(json.dumps(update))
                    if ui_connection:
                        await ui_connection.send_text(json.dumps(update))

                    # ランダムプレイヤーに通知
                    if current_player == 1 and player_connection:
                        await player_connection.send_text("BOARD " + flatten_board(field.board))
                        legal_moves_str = "LEGAL_MOVES " + " ".join(f"{x},{y}" for x, y in field.legal_moves(current_player))
                        await player_connection.send_text(legal_moves_str)
                        await player_connection.send_text(f"FLIP_COUNT {flips_in_human_move}")
                        await player_connection.send_text("your turn")
                        print("Sent board, legal moves, and turn info to random player") #ランダムプレイヤーに送信
                except Exception as e:
                    print("Invalid move:", e)
                    await ws.send_text(json.dumps({"type": "error", "message": str(e)}))

    except WebSocketDisconnect:
        print("Board WS disconnected")