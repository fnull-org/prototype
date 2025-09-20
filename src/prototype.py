# prototype.py
from utils import get_local_ip
from random_code import gen_random_code
from serve import serve_folder
from fetch import fetch_folder
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python prototype.py serve <folder>")
        print("  python prototype.py fetch <url>")
        return

    cmd = sys.argv[1]
    arg = sys.argv[2]
    if cmd == "serve":
        serve_folder(arg)
    elif cmd == "fetch":
        fetch_folder(arg)
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()