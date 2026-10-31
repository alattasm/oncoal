#!/bin/sh
# Usage: ./mux.sh <audio file> [output.mp4]  — put any licensed track on the rendered video (fades out at the end)
set -e
cd "$(dirname "$0")"
ffmpeg -y -loglevel error -i oncoal_promo_nomusic.mp4 -i "$1" -map 0:v -map 1:a -c:v copy \
  -af "afade=t=in:d=0.5,afade=t=out:st=42.5:d=1.5" -c:a aac -b:a 192k -shortest -movflags +faststart "${2:-oncoal_promo.mp4}"
