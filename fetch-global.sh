#!/bin/bash
# This script fetches the latest requirements.txt AND the match.py verification script
# from the master branch of version-repo.

# --- CONFIGURATION ---
# IMPORTANT: Replace with the actual owner/repo name of your version-repo
VERSION_REPO="your-organization/version-repo"
OUTPUT_DIR="constraints"
# --- END CONFIGURATION ---

# Ensure the constraints directory exists
mkdir -p "$OUTPUT_DIR"

# Construct the URLs to the raw files on the master branch
REQS_URL="https://raw.githubusercontent.com/mmheydari97/global-env/refs/heads/main/requirements.txt"
SCRIPT_URL="https://raw.githubusercontent.com/mmheydari97/global-env/refs/heads/main/match.py"

REQS_FILE="$OUTPUT_DIR/requirements.txt"
SCRIPT_FILE="$OUTPUT_DIR/match.py"

echo "Downloading latest production constraints from $REQS_URL..."
if ! curl -s -f -o "$REQS_FILE" "$REQS_URL"; then
  echo "❌ Failed to download requirements.txt."
  echo "   Please check the repository name and that the file exists in the master branch."
  exit 1
fi

echo "Downloading latest verification script from $SCRIPT_URL..."
if ! curl -s -f -o "$SCRIPT_FILE" "$SCRIPT_URL"; then
  echo "❌ Failed to download match.py."
  echo "   Please check the repository name and that the file exists in the master branch."
  exit 1
fi

# Make the downloaded script executable
chmod +x "$SCRIPT_FILE"

echo "✅ Successfully updated local constraints and verification script."

