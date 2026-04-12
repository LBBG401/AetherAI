#!/bin/bash
# ─────────────────────────────────────────
#  AetherAI — Script d'installation Linux
# ─────────────────────────────────────────

set -e

INSTALL_DIR="$HOME/AetherAI"

echo ""
echo "=================================================="
echo "  AetherAI — Installation Linux"
echo "=================================================="
echo ""

# 1. Vérifie/installe Python
echo "→ Vérification Python..."
if ! command -v python3 &>/dev/null; then
    echo "  Installation Python3..."
    sudo apt-get update -q
    sudo apt-get install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION détecté."

# 2. Crée le dossier
echo "→ Création du dossier $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/aether_images"
mkdir -p "$INSTALL_DIR/aether_videos"

# 3. Copie les fichiers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "→ Copie des fichiers..."
for f in aether.py aether_tui.py first_run.py detect.py memory.py cowork.py \
          imagine.py imagine_video.py setup_local.py discord_bot.py requirements.txt; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
        cp "$SCRIPT_DIR/$f" "$INSTALL_DIR/$f"
        echo "  Copié : $f"
    else
        echo "  Manquant : $f"
    fi
done

# 4. Venv + dépendances
echo "→ Création du venv..."
python3 -m venv "$INSTALL_DIR/venv"
echo "→ Installation des dépendances..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# 5. Launchers globaux
echo "→ Création des commandes..."
sudo tee /usr/local/bin/aether > /dev/null << LAUNCHER
#!/bin/bash
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/aether.py"
LAUNCHER

sudo tee /usr/local/bin/aether-tui > /dev/null << LAUNCHER
#!/bin/bash
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/aether_tui.py"
LAUNCHER

sudo chmod +x /usr/local/bin/aether /usr/local/bin/aether-tui
echo "  Commandes 'aether' et 'aether-tui' disponibles."

echo ""
echo "=================================================="
echo "  Installation terminée !"
echo ""
echo "  aether      → terminal classique"
echo "  aether-tui  → interface TUI"
echo "=================================================="
echo ""
