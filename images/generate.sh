#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check dependencies
for cmd in magick exiftool rsvg-convert; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is required but not found on PATH" >&2
        echo "  Install with: brew install imagemagick exiftool librsvg" >&2
        exit 1
    fi
done

# Manifest: each line is "svg_basename:output_path"
ENTRIES="
home_kitchen:example/photos/home/IMG_5892.jpg
home_plant:example/photos/home/IMG_6067.png
home_cat:example/photos/home/funny.gif
home_coffee:example/photos/home/IMG_6340.png
travel_palace:example/photos/travel/palace.jpg
travel_bridge:example/photos/travel/bridge.png
travel_market:example/photos/travel/trip0037.jpeg
travel_pub:example/photos/travel/hotel.webp
travel_temple:example/photos/travel/temple.jpg
travel_garden:example/photos/travel/garden.jpeg
travel_lantern:example/photos/travel/lantern.webp
travel_bamboo:example/photos/travel/bamboo.jpg
"

count=0

for entry in $ENTRIES; do
    name="${entry%%:*}"
    relpath="${entry#*:}"
    svg="$SCRIPT_DIR/${name}.svg"
    output="$PROJECT_DIR/${relpath}"

    if [[ ! -f "$svg" ]]; then
        echo "Warning: $svg not found, skipping" >&2
        continue
    fi

    # Ensure output directory exists
    mkdir -p "$(dirname "$output")"

    # Determine quality flags based on output format
    ext="${output##*.}"
    quality_args=()
    case "$ext" in
        jpg|jpeg) quality_args=(-quality 85) ;;
        webp)     quality_args=(-quality 80) ;;
    esac

    # Render SVG to raster: rsvg-convert for accurate SVG, magick for format conversion
    if [[ "$ext" == "png" ]]; then
        rsvg-convert "$svg" -o "$output"
    else
        rsvg-convert "$svg" | magick png:- ${quality_args[@]+"${quality_args[@]}"} "$output"
    fi
    echo "Generated: $relpath"

    # Extract and apply metadata (skip for GIF — limited metadata support)
    if [[ "$ext" == "gif" ]]; then
        count=$((count + 1))
        continue
    fi

    # Extract metadata lines from SVG comment block
    metadata_args=()
    in_block=false
    while IFS= read -r line; do
        if [[ "$line" == *'<!--METADATA'* ]]; then
            in_block=true
            continue
        fi
        if [[ "$line" == *'METADATA-->'* ]]; then
            in_block=false
            continue
        fi
        if $in_block; then
            trimmed="${line#"${line%%[![:space:]]*}"}"
            if [[ -n "$trimmed" ]]; then
                metadata_args+=("$trimmed")
            fi
        fi
    done < "$svg"

    if [[ ${#metadata_args[@]} -gt 0 ]]; then
        exiftool -overwrite_original "${metadata_args[@]}" "$output" >/dev/null
        echo "  Embedded ${#metadata_args[@]} metadata tags"
    fi

    count=$((count + 1))
done

echo ""
echo "Done: $count images generated."
