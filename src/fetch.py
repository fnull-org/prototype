import os
import requests
from bs4 import BeautifulSoup

def fetch_folder(url, outdir="."):
    if not url.endswith("/"):
        url += "/"

    print(f"[+] Downloading folder from {url}
          ")
    r = requests.get(url)
    if r.status_code != 200:
        print("[-] Cannot connect to server")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    links = [a["href"] for a in soup.find_all("a") if a.get("href") not in ("../", "/")]

    os.makedirs(outdir, exist_ok=True)
    for link in links:
        file_url = url + link
        print(f"  -> {link}")
        res = requests.get(file_url, stream=True)
        with open(os.path.join(outdir, link), "wb") as f:
            for chunk in res.iter_content(8192):
                f.write(chunk)
    print("[+] Done.")