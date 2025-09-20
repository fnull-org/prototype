import os
import http.server
import socketserver
from utils import get_local_ip
from random_code import gen_random_code

PORT = 8000

def serve_folder(folder):
    token = gen_random_code()
    os.chdir(folder)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if path.startswith("/" + token):
                subpath = path[len("/" + token):]
                return os.path.join(folder, subpath.lstrip("/"))
            return "/dev/null"

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        ip = get_local_ip()
        print("Serving folder...")
        print(f"-> http://{ip}:{PORT}/{token}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[+] Server stopped.")