#!/usr/bin/env bash
# Usage: bash fix-tibia.sh [launcher-directory]
# Override TIBIA_DATA_DIR if the game uses another package directory.
set -euo pipefail

PASTA_DADOS="${TIBIA_DATA_DIR:-$HOME/.local/share/CipSoft GmbH/Tibia/packages/Tibia}"
PASTA_JOGO="${1:-${TIBIA_GAME_DIR:-$HOME/Games/Tibia}}"

if [ ! -x "$PASTA_JOGO/Tibia" ]; then
    echo "Tibia launcher not found or not executable: $PASTA_JOGO/Tibia" >&2
    exit 1
fi
if [ ! -d "$PASTA_DADOS" ]; then
    echo "Tibia package directory not found: $PASTA_DADOS" >&2
    exit 1
fi
PASTA_DADOS="$(cd -- "$PASTA_DADOS" && pwd -P)"
PASTA_JOGO="$(cd -- "$PASTA_JOGO" && pwd -P)"
case "$PASTA_DADOS" in
    /|"$HOME"|"$PASTA_JOGO")
        echo "Refusing to clean this directory: $PASTA_DADOS" >&2
        exit 1 ;;
esac

echo "Package directory: $PASTA_DADOS"
echo "Launcher directory: $PASTA_JOGO"
echo "This will close Tibia, back up characterdata/minimap, and remove package files for a fresh download."
read -r -p "Continue? [y/N] " resposta
case "$resposta" in y|Y|s|S) ;; *) echo "Cancelled."; exit 0 ;; esac

pkill -x Tibia 2>/dev/null || true
sleep 1
if pgrep -x Tibia >/dev/null; then
    echo "Tibia is still running. Close it and try again." >&2
    exit 1
fi

BACKUP_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/tibia-backups"
mkdir -p -- "$BACKUP_ROOT"
BACKUP="$(mktemp -d "$BACKUP_ROOT/backup-XXXXXXXX")"
for pasta in characterdata minimap; do
    if [ -d "$PASTA_DADOS/$pasta" ]; then
        cp -a -- "$PASTA_DADOS/$pasta" "$BACKUP/"
    fi
done
# set -e stops the script before deletion if a copy fails.
echo "Backup saved to: $BACKUP"

rm -rf -- "$PASTA_DADOS/bin" "$PASTA_DADOS/assets" "$PASTA_DADOS/sounds" "$PASTA_DADOS/cache"
rm -f -- "$PASTA_DADOS/package.json" "$PASTA_DADOS/package.json.version"     "$PASTA_DADOS/assets.json" "$PASTA_DADOS/assets.json.sha256"

echo "Starting the launcher. Let the downloads finish before pressing Play."
cd -- "$PASTA_JOGO"
exec ./Tibia
