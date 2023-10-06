#!/bin/sh

while IFS= read -r line; do
    if [ -e "./out/$line.txt" ]; then
        echo "File $line exists. Skipping"
    else
        ./ultimate-guitar-scraper  fetch -id $line 1> ./out/$line.txt
        echo "Saved $line"
    fi
done < ultimate_guitar_top_song_ids.json
