#!/bin/bash
# Script to clean the Llama Stack registry and restart the server

echo "=== Cleaning Llama Stack Registry ==="

# Define the database paths
KVSTORE_DB="${SQLITE_STORE_DIR:-~/.llama/distributions/distribution-myenv-ollama}/kvstore.db"
SQL_STORE_DB="${SQLITE_STORE_DIR:-~/.llama/distributions/distribution-myenv-ollama}/sql_store.db"

# Expand the tilde
KVSTORE_DB="${KVSTORE_DB/#\~/$HOME}"
SQL_STORE_DB="${SQL_STORE_DB/#\~/$HOME}"

echo "Database locations:"
echo "  KV Store: $KVSTORE_DB"
echo "  SQL Store: $SQL_STORE_DB"
echo ""

# Check if databases exist
if [ -f "$KVSTORE_DB" ]; then
    echo "⚠️  Found existing KV store database"
    read -p "Delete it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm "$KVSTORE_DB"
        echo "✅ Deleted KV store database"
    else
        echo "❌ Keeping existing database - you may encounter conflicts"
    fi
else
    echo "ℹ️  No existing KV store database found"
fi

if [ -f "$SQL_STORE_DB" ]; then
    echo "⚠️  Found existing SQL store database"
    read -p "Delete it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm "$SQL_STORE_DB"
        echo "✅ Deleted SQL store database"
    else
        echo "❌ Keeping existing database"
    fi
else
    echo "ℹ️  No existing SQL store database found"
fi

echo ""
echo "=== Starting Llama Stack Server ==="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the stack
exec "$SCRIPT_DIR/run-ollama-stack.sh"

