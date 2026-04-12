import os
import sys
import subprocess
import platform
import urllib.request
import json

OLLAMA_FLAG = ".ollama_ready"  # fichier créé après installation réussie

# ─────────────────────────────────────────
#  DÉTECTION OS
# ─────────────────────────────────────────
def get_os() -> str:
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Linux":
        return "linux"
    elif system == "Darwin":
        return "macos"
    return "unknown"

# ─────────────────────────────────────────
#  VÉRIFICATIONS
# ─────────────────────────────────────────
def ollama_installed() -> bool:
    """Vérifie si la commande ollama est disponible."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False

def ollama_running() -> bool:
    """Vérifie si le serveur Ollama tourne sur le port 11434."""
    try:
        with urllib.request.urlopen("http://localhost:11434", timeout=3) as r:
            return True
    except:
        return False

def model_installed(model: str) -> bool:
    """Vérifie si le modèle est déjà téléchargé."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as r:
            data = json.loads(r.read())
            models = [m["name"].split(":")[0] for m in data.get("models", [])]
            return model in models
    except:
        return False

# ─────────────────────────────────────────
#  INSTALLATION OLLAMA
# ─────────────────────────────────────────
def install_ollama(os_name: str) -> bool:
    print("  Installation d'Ollama...")
    try:
        if os_name == "windows":
            # Télécharge l'installeur Windows
            installer_url = "https://ollama.com/download/OllamaSetup.exe"
            installer_path = os.path.join(os.environ.get("TEMP", "."), "OllamaSetup.exe")
            print(f"  Telechargement depuis {installer_url}...")
            urllib.request.urlretrieve(installer_url, installer_path)
            print("  Lancement de l'installeur (suis les instructions)...")
            subprocess.run([installer_path, "/SILENT"], check=True)
            return True

        elif os_name == "linux":
            # Script officiel Ollama pour Linux
            script_url = "https://ollama.com/install.sh"
            print("  Installation via le script officiel Linux...")
            result = subprocess.run(
                f"curl -fsSL {script_url} | sh",
                shell=True, check=True
            )
            return True

        elif os_name == "macos":
            # Vérifie si Homebrew est dispo
            brew = subprocess.run(["which", "brew"], capture_output=True)
            if brew.returncode == 0:
                print("  Installation via Homebrew...")
                subprocess.run(["brew", "install", "ollama"], check=True)
            else:
                print("  Homebrew non trouve. Telechargement manuel...")
                installer_url = "https://ollama.com/download/Ollama-darwin.zip"
                print(f"  Ouvre ce lien pour installer Ollama : {installer_url}")
                return False
            return True

    except Exception as e:
        print(f"  Erreur installation Ollama : {e}")
        return False

# ─────────────────────────────────────────
#  DÉMARRAGE OLLAMA SERVE
# ─────────────────────────────────────────
def start_ollama_serve(os_name: str):
    """Lance ollama serve en arrière-plan."""
    print("  Demarrage du serveur Ollama en arriere-plan...")
    try:
        if os_name == "windows":
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        # Attend que le serveur soit prêt
        import time
        for _ in range(10):
            time.sleep(1)
            if ollama_running():
                print("  Serveur Ollama demarre.")
                return True
        print("  Serveur Ollama long a demarrer — continue quand meme.")
        return True
    except Exception as e:
        print(f"  Impossible de demarrer ollama serve : {e}")
        return False

# ─────────────────────────────────────────
#  TÉLÉCHARGEMENT DU MODÈLE
# ─────────────────────────────────────────
def pull_model(model: str) -> bool:
    print(f"  Telechargement du modele {model} (peut prendre quelques minutes)...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            timeout=600  # 10 minutes max
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  Timeout — le telechargement prend trop de temps.")
        return False
    except Exception as e:
        print(f"  Erreur : {e}")
        return False

# ─────────────────────────────────────────
#  POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────
def setup_ollama(model: str = "tinyllama", silent: bool = False) -> bool:
    """
    Vérifie et installe Ollama + le modèle si nécessaire.
    Retourne True si tout est prêt, False sinon.
    silent=True : n'affiche rien si déjà installé
    """
    os_name = get_os()

    if os_name == "unknown":
        print("OS non supporte pour le mode local.")
        return False

    # Déjà tout installé et prêt ?
    if os.path.exists(OLLAMA_FLAG):
        if not ollama_running():
            start_ollama_serve(os_name)
        return True

    print("\n[Setup Mode Local]")
    print(f"  OS detecte : {os_name}")

    # 1. Installe Ollama si absent
    if not ollama_installed():
        print("  Ollama non detecte.")
        ok = install_ollama(os_name)
        if not ok:
            print("  Installation echouee. Mode local indisponible.")
            return False
        print("  Ollama installe.")
    else:
        print("  Ollama deja installe.")

    # 2. Démarre ollama serve si pas actif
    if not ollama_running():
        start_ollama_serve(os_name)

    # 3. Télécharge le modèle si absent
    if not model_installed(model):
        print(f"  Modele {model} non trouve.")
        ok = pull_model(model)
        if not ok:
            print(f"  Impossible de telecharger {model}.")
            return False
        print(f"  Modele {model} pret.")
    else:
        print(f"  Modele {model} deja present.")

    # 4. Marque comme prêt
    with open(OLLAMA_FLAG, "w") as f:
        f.write(f"{os_name}:{model}")

    print("  Mode local pret !\n")
    return True

if __name__ == "__main__":
    ok = setup_ollama()
    if ok:
        print("Setup termine avec succes.")
    else:
        print("Setup echoue.")
