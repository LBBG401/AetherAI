import platform
import subprocess
import json
import os

CONFIG_FILE = "aether_config.json"

def detect_os():
    system = platform.system()
    if system == "Windows":
        return {
            "os": "Windows",
            "shell": "cmd",
            "commands": {
                "list_dir":   "dir",
                "read_file":  "type",
                "search":     "findstr",
                "clear":      "cls",
                "move":       "move",
                "copy":       "copy",
                "delete":     "del",
                "make_dir":   "mkdir",
                "process":    "tasklist",
                "network":    "ipconfig",
            },
            "forbidden": ["ls", "cat", "grep", "rm", "cp", "mv", "pwd", "touch", "chmod"],
            "prompt": (
                "Tu es sur Windows 11. "
                "Utilise UNIQUEMENT des commandes CMD/PowerShell. "
                "Jamais de commandes Linux (ls, cat, grep, rm, etc.). "
                "Exemples : dir au lieu de ls, type au lieu de cat, del au lieu de rm."
            )
        }
    elif system == "Linux":
        distro = ""
        try:
            result = subprocess.run(["cat", "/etc/os-release"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.startswith("PRETTY_NAME"):
                    distro = line.split("=")[1].strip().strip('"')
                    break
        except:
            distro = "Linux"
        return {
            "os": f"Linux ({distro})",
            "shell": "bash",
            "commands": {
                "list_dir":   "ls",
                "read_file":  "cat",
                "search":     "grep",
                "clear":      "clear",
                "move":       "mv",
                "copy":       "cp",
                "delete":     "rm",
                "make_dir":   "mkdir",
                "process":    "ps aux",
                "network":    "ip a",
            },
            "forbidden": ["dir", "type", "del", "ipconfig", "tasklist", "cls"],
            "prompt": (
                f"Tu es sur {distro}. "
                "Utilise UNIQUEMENT des commandes Bash/Linux. "
                "Jamais de commandes Windows (dir, type, del, ipconfig, etc.)."
            )
        }
    else:
        return {
            "os": system,
            "shell": "sh",
            "commands": {},
            "forbidden": [],
            "prompt": f"Tu es sur {system}. Adapte tes commandes en conséquence."
        }

def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def get_config() -> dict:
    config = detect_os()
    save_config(config)
    return config

if __name__ == "__main__":
    config = get_config()
    print(f"✅ Système détecté : {config['os']}")
    print(f"   Shell          : {config['shell']}")
    print(f"   Config sauvée  : {CONFIG_FILE}")
