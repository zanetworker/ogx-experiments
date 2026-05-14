#!/bin/bash
# Clean OGX databases and restart the server.
# Useful when schema changes cause conflicts with old data.

set -euo pipefail

DIST_DIR="${SQLITE_STORE_DIR:-$HOME/.ogx/distributions/dev-experiments}"

echo "=== Cleaning OGX Databases ==="
echo "Directory: $DIST_DIR"
echo ""

if [ ! -d "$DIST_DIR" ]; then
    echo "No database directory found at $DIST_DIR"
    echo "Starting fresh..."
else
    for db in "$DIST_DIR"/*.db; do
        [ -f "$db" ] || continue
        echo "  Removing: $(basename "$db")"
        rm "$db"
    done
    echo "Done."
fi

echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exec "$SCRIPT_DIR/run-ogx.sh"
