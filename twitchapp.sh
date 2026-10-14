#!/usr/bin/env bash
# Run from any directory. Set TWITCH_APP_VENV to use a different environment.
set -euo pipefail
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
VENV="${TWITCH_APP_VENV:-$DIR/.venv-twitch}"

if [ ! -x "$VENV/bin/python" ]; then
    echo "Creating the Twitch app environment..."
    python3 -m venv "$VENV"
fi

# Recheck requirements so an existing environment also gets missing packages.
"$VENV/bin/python" -m pip install -r "$DIR/requirements-twitch.txt"
export PATH="$VENV/bin:$PATH"
exec "$VENV/bin/python" "$DIR/twitch_app.py"
