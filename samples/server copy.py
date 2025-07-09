import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import argparse, logging, othello_py

def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--games", type=int, default=1)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    othello_py.server_main(
        args.host, args.port, args.games, quiet=args.quiet
    )

if __name__=="__main__":
    main()
