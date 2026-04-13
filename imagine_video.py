
import requests
import time
import os
import platform
import subprocess

SEEDANCE_API_KEY = ""
BASE_URL         = "https://seedanceapi.org/v2"
VIDEO_DIR        = os.path.join(os.path.dirname(__file__), "aether_videos")

def ensure_dir():
    os.makedirs(VIDEO_DIR, exist_ok=True)

def generate_video(prompt, duration=5, model="seedance-2.0-fast"):
    ensure_dir()
    if not SEEDANCE_API_KEY:
        return False, "Cle Seedance manquante."
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            headers={"Authorization": f"Bearer {SEEDANCE_API_KEY}", "Content-Type": "application/json"},
            json={"prompt": prompt, "aspect_ratio": "16:9", "duration": duration, "model": model},
            timeout=30
        )
        data = response.json()
    except Exception as e:
        return False, f"Erreur soumission : {e}"
    if data.get("code") != 200:
        return False, f"Erreur API : {data.get('message', 'inconnue')}"
    task_id = data["data"]["task_id"]
    for attempt in range(36):
        time.sleep(10)
        try:
            r = requests.get(f"{BASE_URL}/status?task_id={task_id}", headers={"Authorization": f"Bearer {SEEDANCE_API_KEY}"}, timeout=15)
            payload = r.json()["data"]
            if payload["status"] == "SUCCESS":
                video_url = payload["response"][0]
                safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in prompt)[:40].strip()
                filepath = os.path.join(VIDEO_DIR, f"{safe_name}.mp4")
                with open(filepath, "wb") as f:
                    f.write(requests.get(video_url, timeout=60).content)
                return True, filepath
            elif payload["status"] == "FAILED":
                return False, f"Echoue : {payload.get('error_message', 'inconnue')}"
        except Exception as e:
            continue
    return False, "Timeout 6 min"

def open_file(filepath):
    system = platform.system()
    try:
        if system == "Windows": os.startfile(filepath)
        elif system == "Linux": subprocess.Popen(["xdg-open", filepath])
        else: subprocess.Popen(["open", filepath])
    except: pass