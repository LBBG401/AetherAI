import json

def get_user_setting(key):
    try:
        with open("aether_user.json", "r") as f:
            settings = json.load(f)
        return settings.get(key)
    except FileNotFoundError:
        return None

        print("aether_user module loaded")