import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "aether_user.json")

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_user_setting(key: str) -> str:
    """Retourne la valeur d'un parametre utilisateur ou chaine vide."""
    return load_config().get(key, "")

def first_run_setup() -> dict:
    print("\n" + "="*50)
    print("  AetherAI — Premier lancement")
    print("="*50 + "\n")

    config = {}

    print("1. Cle Groq API (console.groq.com)")
    while True:
        key = input("   gsk_... : ").strip()
        if key.startswith("gsk_") and len(key) > 20:
            config["groq_key"] = key
            break
        print("   Cle invalide.")

    print("\n2. Cle Pollinations (optionnelle, images)")
    pol = input("   sk_... ou Entree pour ignorer : ").strip()
    config["pollinations_key"] = pol if pol.startswith("sk_") else ""

    print("\n3. Cle Seedance (optionnelle, videos)")
    seed = input("   sk_... ou Entree pour ignorer : ").strip()
    config["seedance_api_key"] = seed if seed.startswith("sk_") else ""

    print("\n4. Cle HeyGen (videos)")
    heygen = input("   Entree ta cle API HeyGen : ").strip()
    config["heygen_api_key"] = heygen if len(heygen) > 10 else ""

    print("\n5. Token Discord Bot (optionnel)")
    disc = input("   Token ou Entree pour ignorer : ").strip()
    config["discord_token"] = disc if len(disc) > 20 else ""

    save_config(config)
    print("\n Configuration sauvegardee !\n" + "="*50 + "\n")
    return config

def get_or_setup() -> dict:
    config = load_config()
    if not config.get("groq_key"):
        config = first_run_setup()
    return config

if __name__ == "__main__":
    config = get_or_setup()
    print(f"Cle Groq : {config.get('groq_key', '')[:10]}...")
