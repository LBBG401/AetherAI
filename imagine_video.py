import requests
from aether_user import get_user_setting

# ─────────────────────────────────────────
#  HEYGEN VIDEO
# ─────────────────────────────────────────
def generate_video_heygen(prompt: str):
    if not HEYGEN_KEY:
        return False, "Aucune clé HeyGen configurée"

    url = "https://api.heygen.com/v2/video/generate"

    payload = {
        "caption": False,
        "dimension": {
            "width": 1920,
            "height": 1080
        }
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": HEYGEN_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return True, response.text
    except Exception as e:
        return False, str(e)

def generate_video():
    # 🔑 récupère la clé depuis ton fichier aether_user.json
    api_key = get_user_setting("heygen_api_key")

    if not api_key:
        print("❌ Aucune clé API HeyGen trouvée dans la config")
        return

    url = "https://api.heygen.com/v2/video/generate"

    payload = {
        "caption": False,
        "dimension": {
            "width": 1920,
            "height": 1080
        }
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        print("\n--- Réponse API :contentReference[oaicite:0]{index=0} ---")
        print("Status:", response.status_code)
        print("Body:", response.text)

    except Exception as e:
        print("❌ Erreur :", e)


if __name__ == "__main__":
    generate_video()