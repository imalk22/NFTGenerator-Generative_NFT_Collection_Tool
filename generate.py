import argparse
import json
import random
import sys
from pathlib import Path

from nftgen.config import load_config
from nftgen.traits import scan_layers, TraitFolderError, TraitFileError
from nftgen.compose import (
    max_unique_combinations,
    pick_combination,
    detect_canvas_size,
    composite_image,
    CapacityError,
)
from nftgen.metadata import build_metadata
from nftgen.report import build_rarity_report, print_rarity_report


def prompt_for_count() -> int:
    while True:
        raw = input("How many NFTs do you want to generate? ").strip()
        try:
            count = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if count <= 0:
            print("Please enter a number greater than 0.")
            continue
        return count


def main():
    parser = argparse.ArgumentParser(description="Generate a layered NFT collection.")
    parser.add_argument("--count", type=int, default=None, help="Number of NFTs to generate")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        folders = scan_layers(config.layers_dir)
        max_unique = max_unique_combinations(folders)
        canvas_size = detect_canvas_size(folders)
    except (FileNotFoundError, TraitFolderError, TraitFileError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    count = args.count if args.count is not None else prompt_for_count()

    if count > max_unique:
        print(
            f"Error: requested {count} images, but only {max_unique} unique "
            f"trait combinations are possible with the current layers. "
            f"Add more trait options, or request {max_unique} or fewer."
        )
        sys.exit(1)

    output_dir = Path(config.output_dir)
    images_dir = output_dir / "images"
    metadata_dir = output_dir / "metadata"
    images_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random()

    seen = set()
    combos = []
    progress_interval = max(1, count // 20)

    for i in range(count):
        combo = pick_combination(folders, seen, rng)
        seen.add(combo)
        combos.append(combo)

        edition = config.start_edition + i
        image = composite_image(folders, combo, canvas_size)
        image.save(images_dir / f"{edition}.png")

        metadata = build_metadata(
            folders, combo, edition, config.name, config.description,
        )
        with open(metadata_dir / f"{edition}.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        if (i + 1) % progress_interval == 0 or (i + 1) == count:
            print(f"Generated {i + 1}/{count}")

    report = build_rarity_report(folders, combos)
    print_rarity_report(report, len(combos), max_unique)
    print(f"\nDone. Images in {images_dir}, metadata in {metadata_dir}.")


if __name__ == "__main__":
    try:
        main()
    except CapacityError as e:
        print(f"Error: {e}")
        sys.exit(1)
