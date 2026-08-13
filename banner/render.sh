#!/usr/bin/env bash
# Przelicza statystyki jezykow i sklada baner do pliki/hero-panda.gif.
#
#   ./banner/render.sh
#
# Wymaga: ffmpeg, python3 z Pillow, gh (zalogowany albo GH_TOKEN w srodowisku).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out="$here/../pliki/hero-panda.gif"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

python3 "$here/fetch_stats.py" "$work/stats.json"

# klatka do probkowania kolorow na styku zdjecia i panelu
ffmpeg -y -v error -ss 2 -i "$here/source.mp4" -frames:v 1 "$work/edge.png"

python3 "$here/make_banner.py" "$work/edge.png" "$work/stats.json" \
    "$work/banner.png"

# panel jest domalowany do plotna gifa, a nie osobnym obrazkiem pod nim -
# GitHub wstawia miedzy dwa obrazki odstep i szew bylby widoczny
ffmpeg -y -v error -i "$here/source.mp4" -i "$work/banner.png" \
    -filter_complex "[0:v]pad=1010:492:0:0:color=black,fps=10[v];\
[v][1:v]overlay=0:0[o];[o]split[a][b];\
[a]palettegen=stats_mode=diff:max_colors=128[p];\
[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
    -loop 0 "$out"

echo "$out: $(du -h "$out" | cut -f1)"
