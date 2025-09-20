import http.server
import socketserver
import os
import sys
import secrets
import string
import socket
import threading
import time
import argparse
import zipfile
import tempfile
from urllib.parse import unquote
from pathlib import Path

class TokenHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, token=None, shared_path=None, is_file=False, **kwargs):
        self.token = token
        self.shared_path = shared_path
        self.is_file = is_file
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        path_parts = self.path.strip('/').split('/')
        
        if not path_parts or path_parts[0] != self.token:
            self.send_error(404, "Invalid token or path not found")
            return
        
        if self.is_file:
            if len(path_parts) == 1:
                self.serve_single_file(download=True)
                return
            elif len(path_parts) == 2 and path_parts[1] == 'download':
                self.serve_single_file(download=True)
                return
        
        if len(path_parts) == 2 and path_parts[1] == 'download.zip':
            self.serve_folder_as_zip()
            return
        
        if len(path_parts) == 1:
            self.path = '/'
        else:
            self.path = '/' + '/'.join(path_parts[1:])
        
        original_cwd = os.getcwd()
        try:
            if self.is_file:
                os.chdir(os.path.dirname(self.shared_path))
            else:
                os.chdir(self.shared_path)
            super().do_GET()
        finally:
            os.chdir(original_cwd)
    
    def serve_single_file(self, download=False):
        try:
            with open(self.shared_path, 'rb') as f:
                file_size = os.path.getsize(self.shared_path)
                filename = os.path.basename(self.shared_path)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(file_size))
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")
    
    def serve_folder_as_zip(self):
        try:
            folder_name = os.path.basename(self.shared_path)
            zip_filename = f"{folder_name}.zip"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(self.shared_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.shared_path)
                            zipf.write(file_path, arcname)
                
                zip_size = os.path.getsize(temp_zip.name)
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                self.send_header('Content-Length', str(zip_size))
                self.send_header('Content-Disposition', f'attachment; filename="{zip_filename}"')
                self.end_headers()
                
                with open(temp_zip.name, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                
                os.unlink(temp_zip.name)
                
        except Exception as e:
            self.send_error(500, f"Error creating zip: {e}")

def generate_token(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def start_server(shared_path, port=8000):
    
    if not os.path.exists(shared_path):
        print(f"Error: Path '{shared_path}' does not exist")
        return
    
    is_file = os.path.isfile(shared_path)
    is_dir = os.path.isdir(shared_path)
    
    if not is_file and not is_dir:
        print(f"Error: '{shared_path}' is neither a file nor a directory")
        return
    
    token = generate_token()
    
    local_ip = get_local_ip()
    
    def handler_factory(*args, **kwargs):
        return TokenHTTPRequestHandler(*args, token=token, shared_path=shared_path, is_file=is_file, **kwargs)
    
    try:
        with socketserver.TCPServer(("", port), handler_factory) as httpd:
            print("=" * 50)
            print("🚀 fnull Phase 1 - Local File Sharing")
            print("=" * 50)
            print(f"📁 Sharing: {os.path.abspath(shared_path)}")
            print(f"📄 Type: {'File' if is_file else 'Directory'}")
            print(f"🔑 Token: {token}")
            print(f"🌐 Local URL: http://{local_ip}:{port}/{token}/")
            print(f"🏠 Localhost: http://localhost:{port}/{token}/")
            print("=" * 50)
            print("📋 Share this link with others on your network:")
            print(f"   http://{local_ip}:{port}/{token}/")
            if not is_file:
                print(f"📦 Direct folder download: http://{local_ip}:{port}/{token}/download.zip")
            else:
                print(f"⬇️  Direct file download: http://{local_ip}:{port}/{token}/download")
            print("=" * 50)
            print("Press Ctrl+C to stop the server")
            print()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except OSError as e:
        if e.errno == 48:
            print(f"❌ Error: Port {port} is already in use")
            print(f"💡 Try a different port: python fnull.py '{shared_path}' --port {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")

def download_from_link(url):
    import urllib.request
    import urllib.parse
    
    print(f"🔗 Attempting to access: {url}")
    
    try:
        with urllib.request.urlopen(url) as response:
            content_type = response.headers.get('Content-Type', '')
            
            if 'text/html' in content_type:
                content = response.read().decode('utf-8')
                if "Index of" in content:
                    print("📂 Directory listing found!")
                    print("💡 Available options:")
                    print(f"   🌐 Browse: {url}")
                    print(f"   📦 Download as ZIP: {url}download.zip")
                    print("   Or browse the URL to download individual files")
                else:
                    print("📄 HTML content found - this might be a file listing")
                    print(f"   Open this URL in your browser: {url}")
            else:
                print("📄 File found - downloading...")
                parsed_url = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed_url.path.rstrip('/')) or "downloaded_file"
                
                content = response.read()
                with open(filename, 'wb') as f:
                    f.write(content)
                print(f"✅ Downloaded: {filename} ({len(content)} bytes)")
                
    except Exception as e:
        print(f"❌ Error accessing link: {e}")
        print("💡 Make sure the host is online and the link is correct")

def main():
    parser = argparse.ArgumentParser(
        description="fnull Phase 1 - Local file sharing with HTTP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fnull.py /path/to/folder          # Share a folder
  python fnull.py /path/to/file.txt        # Share a single file
  python fnull.py /path/to/folder --port 9000  # Use custom port
  python fnull.py --download http://192.168.1.100:8000/abc123/  # Download from link
        """
    )
    
    parser.add_argument('path', nargs='?', help='Path to file or folder to share')
    parser.add_argument('--port', type=int, default=8000, help='Port to use (default: 8000)')
    parser.add_argument('--download', metavar='URL', help='Download from a fnull link')
    
    args = parser.parse_args()
    
    if args.download:
        download_from_link(args.download)
    elif args.path:
        start_server(args.path, args.port)
    else:
        parser.print_help()
        print("\n🚀 Quick start:")
        print("  python fnull.py /path/to/your/folder")
        print("  python fnull.py /path/to/your/file.txt")

if __name__ == "__main__":
    main()
