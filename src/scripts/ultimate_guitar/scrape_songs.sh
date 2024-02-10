#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_DIR="$(realpath "$SCRIPT_DIR/../../../out")"

if [ ! -e "$OUT_DIR/ultimate_guitar_top_song_ids.txt" ]; then
    echo "Top song IDs is not generated yet."
    exit 1
fi

mkdir -p "$OUT_DIR/songs"

while IFS= read -r line; do
    if [ -e "$OUT_DIR/songs/$line.txt" ]; then
        echo "File $line exists. Skipping"
    else
        "$SCRIPT_DIR/ultimate-guitar-scraper" fetch -id $line 1> "$OUT_DIR/songs/$line.txt"
        echo "Saved $line"
    fi
done < "$OUT_DIR/ultimate_guitar_top_song_ids.txt"
