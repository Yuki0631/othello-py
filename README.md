# othello-py
ついたてオセロ \
元ののsubmarine-pyからの変更点は、srcファイルと、samplesファイル、およびbatch_run.pyの追加のみ\
ポート番号は8000\
ターミナル上で実行するためには、 \
python samples/server.py \
python samples/hoge_player.py localhost 8000 \
python samples/huga_player.py localhost 8000 \
を3つのターミナルで実行すればよい。 \
何度も一度に対戦させたい場合は、 \
python samples/server.py --host 127.0.0.1 --port 8000 --games {game数} --quiet \
python batch_run.py \
を2つのターミナルで実行すればよい。対戦プレイヤーやgame数は、batch_run.pyを都度変更すればよい。 \
ただし、isMinimax_player.pyを先手にすると、I/Oデッドロックなどにより動作しないため、先手番はターミナルで実行するしかない(いつか修正します)。
