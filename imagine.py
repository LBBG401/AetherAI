import urllib.request
import urllib.parse
import os
import subprocess
import platform

# ─────────────────────────────────────────
#  CONFIG (injecte depuis aether.py)
# ─────────────────────────────────────────
POLLINATIONS_API_KEY = ""

IMAGE_URL = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&model=flux&nologo=true&enhance=true"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "aether_images")

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> tuple:
    ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in prompt)[:40].strip()
    filepath  = os.path.join(OUTPUT_DIR, f"{safe_name}.png")
    encoded   = urllib.parse.quote(prompt)
    url       = IMAGE_URL.format(prompt=encoded, w=width, h=height)
    try:
        headers = {"User-Agent": "AetherAI/1.0"}
        if POLLINATIONS_API_KEY:
            headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 1000:
            return False, "Image non generee — reponse trop courte."
        with open(filepath, "wb") as f:
            f.write(data)
        return True, filepath
    except Exception as e:
        return False, f"Erreur image : {e}"

def open_image(filepath: str):
    open_file(filepath)

def open_file(filepath: str):
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Linux":
            subprocess.Popen(["xdg-open", filepath])
        else:
            subprocess.Popen(["open", filepath])
    except Exception as e:
        print(f"Impossible d'ouvrir : {e}")

if __name__ == "__main__":
    print("Test generation image...")
    ok, result = generate_image("a realistic sunset over the ocean")
    print(f"{'OK' if ok else 'ERREUR'} : {result}")
