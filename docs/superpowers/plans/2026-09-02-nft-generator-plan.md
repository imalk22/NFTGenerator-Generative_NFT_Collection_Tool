# NFT Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that composites weighted, layered trait PNGs into a large collection of unique NFT images with matching ERC-721-style metadata, per `docs/superpowers/specs/2026-09-02-nft-generator-design.md`.

**Architecture:** A small `nftgen/` package with one pure-logic module per responsibility (config loading, trait scanning/parsing, weighted-unique selection + compositing, metadata building, rarity reporting), driven by a thin `generate.py` CLI entrypoint. Pure logic (parsing, weight math, metadata shape) is unit-tested with pytest; image I/O is verified via an end-to-end run against generated demo assets.

**Tech Stack:** Python 3, Pillow (image compositing), pytest (tests), stdlib `argparse`/`json`/`random`.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `nftgen/__init__.py`
- Create: `.gitignore`
- Create: `config.json`

- [ ] **Step 1: Create requirements files**

`requirements.txt`:
```
Pillow>=10.0.0
```

`requirements-dev.txt`:
```
-r requirements.txt
pytest>=7.0.0
```

- [ ] **Step 2: Create empty package init**

`nftgen/__init__.py`:
```python
```

- [ ] **Step 3: Create .gitignore**

`.gitignore`:
```
__pycache__/
*.pyc
output/
.pytest_cache/
```

- [ ] **Step 4: Create default config.json**

`config.json`:
```json
{
  "name": "My Collection",
  "description": "A collection of unique generated NFTs.",
  "symbol": "MYNFT",
  "layers_dir": "layers",
  "output_dir": "output",
  "start_edition": 1
}
```

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements-dev.txt`
Expected: Pillow and pytest install successfully.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt requirements-dev.txt nftgen/__init__.py .gitignore config.json
git commit -m "chore: scaffold NFT generator project"
```

---

### Task 2: Config loading (`nftgen/config.py`)

**Files:**
- Create: `nftgen/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
import json
from pathlib import Path

from nftgen.config import load_config


def test_load_config_applies_defaults_for_missing_fields(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"name": "Custom Name"}))

    config = load_config(config_path)

    assert config.name == "Custom Name"
    assert config.description == "A collection of unique generated NFTs."
    assert config.symbol == "COLLECTION"
    assert config.layers_dir == "layers"
    assert config.output_dir == "output"
    assert config.start_edition == 1


def test_load_config_reads_all_fields(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "name": "My Collection",
        "description": "desc",
        "symbol": "MYNFT",
        "layers_dir": "custom_layers",
        "output_dir": "custom_output",
        "start_edition": 5,
    }))

    config = load_config(config_path)

    assert config.name == "My Collection"
    assert config.description == "desc"
    assert config.symbol == "MYNFT"
    assert config.layers_dir == "custom_layers"
    assert config.output_dir == "custom_output"
    assert config.start_edition == 5


def test_load_config_missing_file_raises(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"

    try:
        load_config(missing_path)
        assert False, "expected FileNotFoundError"
    except FileNotFoundError as e:
        assert "does_not_exist.json" in str(e)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nftgen.config'`

- [ ] **Step 3: Write implementation**

`nftgen/config.py`:
```python
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    name: str
    description: str
    symbol: str
    layers_dir: str
    output_dir: str
    start_edition: int


DEFAULTS = {
    "name": "Unnamed Collection",
    "description": "A collection of unique generated NFTs.",
    "symbol": "COLLECTION",
    "layers_dir": "layers",
    "output_dir": "output",
    "start_edition": 1,
}


def load_config(config_path: Path) -> Config:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    merged = {**DEFAULTS, **raw}
    return Config(
        name=merged["name"],
        description=merged["description"],
        symbol=merged["symbol"],
        layers_dir=merged["layers_dir"],
        output_dir=merged["output_dir"],
        start_edition=int(merged["start_edition"]),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add nftgen/config.py tests/test_config.py
git commit -m "feat: add config.json loading with defaults"
```

---

### Task 3: Trait scanning and parsing (`nftgen/traits.py`)

**Files:**
- Create: `nftgen/traits.py`
- Test: `tests/test_traits.py`

- [ ] **Step 1: Write the failing test**

`tests/test_traits.py`:
```python
from pathlib import Path

import pytest

from nftgen.traits import TraitFolderError, TraitFileError, scan_layers


def make_png(path: Path):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (10, 10), (255, 0, 0, 255)).save(path)


def test_scan_layers_parses_order_type_value_weight(tmp_path):
    make_png(tmp_path / "1_Background" / "Blue#30.png")
    make_png(tmp_path / "1_Background" / "Red#10.png")
    make_png(tmp_path / "2_Eyes" / "Green#5.png")

    folders = scan_layers(tmp_path)

    assert [f.trait_type for f in folders] == ["Background", "Eyes"]
    bg = folders[0]
    assert bg.order == 1
    values = {opt.value: opt.weight for opt in bg.options}
    assert values == {"Blue": 30, "Red": 10}


def test_scan_layers_sorts_by_order_then_name(tmp_path):
    make_png(tmp_path / "2_Zebra" / "A#1.png")
    make_png(tmp_path / "2_Apple" / "A#1.png")
    make_png(tmp_path / "1_Background" / "A#1.png")

    folders = scan_layers(tmp_path)

    assert [f.trait_type for f in folders] == ["Background", "Apple", "Zebra"]


def test_scan_layers_none_value_has_no_filepath(tmp_path):
    make_png(tmp_path / "1_Accessories" / "None#50.png")
    make_png(tmp_path / "1_Accessories" / "Hat#10.png")

    folders = scan_layers(tmp_path)

    options = {opt.value: opt for opt in folders[0].options}
    assert options["None"].filepath is None
    assert options["Hat"].filepath is not None


def test_scan_layers_underscore_becomes_space(tmp_path):
    make_png(tmp_path / "1_Body_Type" / "Gold_Chain#5.png")

    folders = scan_layers(tmp_path)

    assert folders[0].trait_type == "Body Type"
    assert folders[0].options[0].value == "Gold Chain"

def test_scan_layers_missing_layers_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        scan_layers(tmp_path / "does_not_exist")


def test_scan_layers_empty_trait_folder_raises(tmp_path):
    (tmp_path / "1_Background").mkdir(parents=True)

    with pytest.raises(TraitFolderError):
        scan_layers(tmp_path)


def test_scan_layers_malformed_filename_raises(tmp_path):
    make_png(tmp_path / "1_Background" / "NoWeightHere.png")

    with pytest.raises(TraitFileError):
        scan_layers(tmp_path)


def test_scan_layers_ignores_non_png_files(tmp_path):
    make_png(tmp_path / "1_Background" / "Blue#30.png")
    (tmp_path / "1_Background" / ".DS_Store").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "1_Background" / "notes.txt").write_text("hi")

    folders = scan_layers(tmp_path)

    assert len(folders[0].options) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_traits.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nftgen.traits'`

- [ ] **Step 3: Write implementation**

`nftgen/traits.py`:
```python
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class TraitFolderError(Exception):
    pass


class TraitFileError(Exception):
    pass


FOLDER_PATTERN = re.compile(r"^(\d+)_(.+)$")
FILE_PATTERN = re.compile(r"^(.+)#(\d+)\.png$", re.IGNORECASE)


@dataclass
class TraitOption:
    value: str
    weight: int
    filepath: Optional[Path]  # None means "absent" (value == "None")


@dataclass
class TraitFolder:
    order: int
    trait_type: str
    options: List[TraitOption]


def _parse_folder_name(name: str) -> tuple:
    match = FOLDER_PATTERN.match(name)
    if not match:
        raise TraitFolderError(
            f"Trait folder '{name}' does not match the required "
            f"'<order>_<TraitType>' naming pattern, e.g. '1_Background'."
        )
    order_str, trait_type_raw = match.groups()
    trait_type = trait_type_raw.replace("_", " ")
    return int(order_str), trait_type


def _parse_file_name(folder_name: str, filename: str) -> tuple:
    match = FILE_PATTERN.match(filename)
    if not match:
        raise TraitFileError(
            f"File '{filename}' in trait folder '{folder_name}' does not match "
            f"the required '<Value>#<Weight>.png' naming pattern, "
            f"e.g. 'Blue#30.png'."
        )
    value_raw, weight_str = match.groups()
    value = value_raw.replace("_", " ")
    weight = int(weight_str)
    if weight <= 0:
        raise TraitFileError(
            f"File '{filename}' in trait folder '{folder_name}' has a weight of "
            f"{weight}; weights must be positive integers."
        )
    return value, weight


def scan_layers(layers_dir) -> List[TraitFolder]:
    layers_dir = Path(layers_dir)
    if not layers_dir.is_dir():
        raise FileNotFoundError(f"Layers directory not found: {layers_dir}")

    subfolders = sorted(
        (p for p in layers_dir.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )
    if not subfolders:
        raise TraitFolderError(f"No trait folders found inside {layers_dir}")

    trait_folders = []
    for folder in subfolders:
        order, trait_type = _parse_folder_name(folder.name)

        png_files = sorted(
            p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"
        )
        if not png_files:
            raise TraitFolderError(
                f"Trait folder '{folder.name}' contains no .png files."
            )

        options = []
        for png_path in png_files:
            value, weight = _parse_file_name(folder.name, png_path.name)
            filepath = None if value.lower() == "none" else png_path
            options.append(TraitOption(value=value, weight=weight, filepath=filepath))

        trait_folders.append(
            TraitFolder(order=order, trait_type=trait_type, options=options)
        )

    trait_folders.sort(key=lambda f: (f.order, f.trait_type))
    return trait_folders
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_traits.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add nftgen/traits.py tests/test_traits.py
git commit -m "feat: scan and parse trait layer folders"
```

---

### Task 4: Weighted-unique selection + capacity check (`nftgen/compose.py`, non-image parts)

**Files:**
- Create: `nftgen/compose.py`
- Test: `tests/test_compose.py`

- [ ] **Step 1: Write the failing test**

`tests/test_compose.py`:
```python
import random

import pytest

from nftgen.traits import TraitFolder, TraitOption
from nftgen.compose import max_unique_combinations, pick_combination, CapacityError


def make_folders():
    return [
        TraitFolder(1, "Background", [
            TraitOption("Blue", 30, "blue.png"),
            TraitOption("Red", 10, "red.png"),
        ]),
        TraitFolder(2, "Accessory", [
            TraitOption("None", 50, None),
            TraitOption("Hat", 10, "hat.png"),
        ]),
    ]


def test_max_unique_combinations_multiplies_option_counts():
    assert max_unique_combinations(make_folders()) == 2 * 2


def test_pick_combination_avoids_duplicates():
    folders = make_folders()
    rng = random.Random(0)
    seen = set()
    combos = []
    for _ in range(4):
        combo = pick_combination(folders, seen, rng)
        seen.add(combo)
        combos.append(combo)

    assert len(set(combos)) == 4
    assert set(combos) == {
        ("Blue", "None"), ("Blue", "Hat"), ("Red", "None"), ("Red", "Hat"),
    }


def test_pick_combination_raises_when_exhausted():
    folders = make_folders()
    rng = random.Random(0)
    seen = {("Blue", "None"), ("Blue", "Hat"), ("Red", "None"), ("Red", "Hat")}

    with pytest.raises(CapacityError):
        pick_combination(folders, seen, rng)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_compose.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nftgen.compose'`

- [ ] **Step 3: Write implementation**

`nftgen/compose.py`:
```python
import random
from math import prod
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from PIL import Image

from nftgen.traits import TraitFolder, TraitFolderError


class CapacityError(Exception):
    pass


def max_unique_combinations(folders: List[TraitFolder]) -> int:
    return prod(len(folder.options) for folder in folders)


def pick_combination(
    folders: List[TraitFolder],
    seen: Set[Tuple[str, ...]],
    rng: random.Random,
    max_attempts: int = 10000,
) -> Tuple[str, ...]:
    for _ in range(max_attempts):
        combo = tuple(
            rng.choices(
                [opt.value for opt in folder.options],
                weights=[opt.weight for opt in folder.options],
                k=1,
            )[0]
            for folder in folders
        )
        if combo not in seen:
            return combo

    raise CapacityError(
        "Could not find a new unique trait combination after "
        f"{max_attempts} attempts; the trait pool may be exhausted."
    )


def detect_canvas_size(folders: List[TraitFolder]) -> Tuple[int, int]:
    first_folder = folders[0]
    available = [opt for opt in first_folder.options if opt.filepath is not None]
    if not available:
        raise TraitFolderError(
            f"Trait folder '{first_folder.trait_type}' has no actual image "
            f"files (all options are 'None'), so canvas size can't be "
            f"detected from it."
        )
    first_option = min(available, key=lambda opt: opt.value)
    with Image.open(first_option.filepath) as img:
        return img.size


def composite_image(
    folders: List[TraitFolder],
    combo: Tuple[str, ...],
    canvas_size: Tuple[int, int],
) -> Image.Image:
    value_to_filepath: Dict[str, Optional[Path]] = {}
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    for folder, value in zip(folders, combo):
        option = next(opt for opt in folder.options if opt.value == value)
        if option.filepath is None:
            continue

        with Image.open(option.filepath) as layer_img:
            layer_img = layer_img.convert("RGBA")
            if layer_img.size != canvas_size:
                print(
                    f"Warning: '{option.filepath}' is {layer_img.size}, "
                    f"expected {canvas_size}. Resizing to fit."
                )
                layer_img = layer_img.resize(canvas_size, Image.LANCZOS)
            canvas.alpha_composite(layer_img)

    return canvas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_compose.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add nftgen/compose.py tests/test_compose.py
git commit -m "feat: weighted unique combination selection and image compositing"
```

---

### Task 5: Metadata building (`nftgen/metadata.py`)

**Files:**
- Create: `nftgen/metadata.py`
- Test: `tests/test_metadata.py`

- [ ] **Step 1: Write the failing test**

`tests/test_metadata.py`:
```python
from nftgen.traits import TraitFolder, TraitOption
from nftgen.metadata import build_metadata


def make_folders():
    return [
        TraitFolder(1, "Background", [TraitOption("Blue", 30, "blue.png")]),
        TraitFolder(2, "Accessory", [
            TraitOption("None", 50, None),
            TraitOption("Hat", 10, "hat.png"),
        ]),
    ]


def test_build_metadata_includes_present_traits():
    folders = make_folders()
    combo = ("Blue", "Hat")

    meta = build_metadata(
        folders, combo, edition=3, collection_name="My Collection",
        description="desc",
    )

    assert meta["name"] == "My Collection #3"
    assert meta["description"] == "desc"
    assert meta["image"] == "3.png"
    assert meta["edition"] == 3
    assert meta["attributes"] == [
        {"trait_type": "Background", "value": "Blue"},
        {"trait_type": "Accessory", "value": "Hat"},
    ]


def test_build_metadata_omits_none_valued_traits():
    folders = make_folders()
    combo = ("Blue", "None")

    meta = build_metadata(
        folders, combo, edition=1, collection_name="My Collection",
        description="desc",
    )

    assert meta["attributes"] == [
        {"trait_type": "Background", "value": "Blue"},
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_metadata.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nftgen.metadata'`

- [ ] **Step 3: Write implementation**

`nftgen/metadata.py`:
```python
from typing import List, Tuple

from nftgen.traits import TraitFolder


def build_metadata(
    folders: List[TraitFolder],
    combo: Tuple[str, ...],
    edition: int,
    collection_name: str,
    description: str,
) -> dict:
    attributes = [
        {"trait_type": folder.trait_type, "value": value}
        for folder, value in zip(folders, combo)
        if value.lower() != "none"
    ]

    return {
        "name": f"{collection_name} #{edition}",
        "description": description,
        "image": f"{edition}.png",
        "edition": edition,
        "attributes": attributes,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_metadata.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add nftgen/metadata.py tests/test_metadata.py
git commit -m "feat: build ERC-721-style metadata per generated image"
```

---

### Task 6: Rarity report (`nftgen/report.py`)

**Files:**
- Create: `nftgen/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write the failing test**

`tests/test_report.py`:
```python
from nftgen.traits import TraitFolder, TraitOption
from nftgen.report import build_rarity_report


def test_build_rarity_report_counts_and_percentages():
    folders = [
        TraitFolder(1, "Background", [
            TraitOption("Blue", 30, "blue.png"),
            TraitOption("Red", 10, "red.png"),
        ]),
    ]
    combos = [("Blue",), ("Blue",), ("Blue",), ("Red",)]

    report = build_rarity_report(folders, combos)

    assert report["Background"]["Blue"]["count"] == 3
    assert report["Background"]["Blue"]["percent"] == 75.0
    assert report["Background"]["Red"]["count"] == 1
    assert report["Background"]["Red"]["percent"] == 25.0


def test_build_rarity_report_includes_zero_count_options():
    folders = [
        TraitFolder(1, "Background", [
            TraitOption("Blue", 30, "blue.png"),
            TraitOption("Gold", 1, "gold.png"),
        ]),
    ]
    combos = [("Blue",)]

    report = build_rarity_report(folders, combos)

    assert report["Background"]["Gold"]["count"] == 0
    assert report["Background"]["Gold"]["percent"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nftgen.report'`

- [ ] **Step 3: Write implementation**

`nftgen/report.py`:
```python
from typing import List, Tuple

from nftgen.traits import TraitFolder


def build_rarity_report(folders: List[TraitFolder], combos: List[Tuple[str, ...]]) -> dict:
    total = len(combos)
    report = {}

    for i, folder in enumerate(folders):
        value_counts = {opt.value: 0 for opt in folder.options}
        for combo in combos:
            value_counts[combo[i]] += 1

        report[folder.trait_type] = {
            value: {
                "count": count,
                "percent": round((count / total) * 100, 2) if total else 0.0,
            }
            for value, count in value_counts.items()
        }

    return report


def print_rarity_report(report: dict, total: int, max_unique: int) -> None:
    print("\n--- Rarity Report ---")
    for trait_type, values in report.items():
        print(f"\n{trait_type}:")
        for value, stats in sorted(values.items(), key=lambda kv: -kv[1]["count"]):
            print(f"  {value}: {stats['count']} / {total} ({stats['percent']}%)")
    print(f"\nUnique combinations used: {total} / {max_unique} possible")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_report.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add nftgen/report.py tests/test_report.py
git commit -m "feat: build and print post-run rarity report"
```

---

### Task 7: CLI entrypoint (`generate.py`)

**Files:**
- Create: `generate.py`

- [ ] **Step 1: Write the entrypoint**

`generate.py`:
```python
import argparse
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

import json


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
```

- [ ] **Step 2: Commit**

```bash
git add generate.py
git commit -m "feat: add CLI entrypoint wiring config, traits, compose, metadata, report"
```

---

### Task 8: Demo asset generator (`scripts/make_demo_assets.py`)

**Files:**
- Create: `scripts/make_demo_assets.py`

- [ ] **Step 1: Write the script**

`scripts/make_demo_assets.py`:
```python
"""One-time helper: generates placeholder colored-shape PNGs into layers/
so the generator can be run end-to-end before real artwork is added."""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = (512, 512)
LAYERS_DIR = Path(__file__).resolve().parent.parent / "layers"


def solid_background(color):
    img = Image.new("RGBA", SIZE, color)
    return img


def circle_layer(color):
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 100
    draw.ellipse([margin, margin, SIZE[0] - margin, SIZE[1] - margin], fill=color)
    return img


def ring_layer(color, width=20):
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 60
    draw.ellipse(
        [margin, margin, SIZE[0] - margin, SIZE[1] - margin],
        outline=color, width=width,
    )
    return img


def star_layer(color):
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy, r = SIZE[0] // 2, 140, 60
    points = []
    import math
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r / 2.5
        points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    draw.polygon(points, fill=color)
    return img


def save(img, folder_name, filename):
    folder = LAYERS_DIR / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    img.save(folder / filename)


def main():
    save(solid_background((80, 150, 255, 255)), "1_Background", "Blue#30.png")
    save(solid_background((255, 120, 80, 255)), "1_Background", "Orange#30.png")
    save(solid_background((60, 60, 60, 255)), "1_Background", "Dark#10.png")

    save(circle_layer((240, 220, 180, 255)), "2_Body", "Tan#40.png")
    save(circle_layer((180, 140, 100, 255)), "2_Body", "Brown#30.png")
    save(circle_layer((255, 215, 0, 255)), "2_Body", "Gold#2.png")

    save(ring_layer((30, 30, 30, 255)), "3_Eyes", "Black#40.png")
    save(ring_layer((0, 150, 0, 255)), "3_Eyes", "Green#20.png")

    save(Image.new("RGBA", SIZE, (0, 0, 0, 0)), "4_Accessories", "None#50.png")
    save(star_layer((255, 0, 0, 255)), "4_Accessories", "Red_Star#15.png")
    save(star_layer((255, 215, 0, 255)), "4_Accessories", "Gold_Star#1.png")

    print(f"Demo trait assets written to {LAYERS_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python scripts/make_demo_assets.py`
Expected: `Demo trait assets written to .../layers` and PNG files created under `layers/1_Background/`, `layers/2_Body/`, `layers/3_Eyes/`, `layers/4_Accessories/`.

- [ ] **Step 3: Commit**

```bash
git add scripts/make_demo_assets.py
git commit -m "feat: add demo trait asset generator for end-to-end testing"
```

---

### Task 9: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Generate a small demo collection**

Run: `python generate.py --count 15`
Expected: Prints progress lines, a rarity report showing Gold/Gold Star appearing rarely, "Unique combinations used: 15 / <max>", and "Done." message.

- [ ] **Step 3: Verify output files**

Run: `python -c "import os; print(len(os.listdir('output/images')), len(os.listdir('output/metadata')))"`
Expected: `15 15`

- [ ] **Step 4: Spot-check one metadata file matches its image**

Run: `python -c "import json; print(json.load(open('output/metadata/1.json')))"`
Expected: Valid JSON with `name`, `image: "1.png"`, `edition: 1`, and an `attributes` list with 3-4 entries (Background, Body, Eyes, optionally Accessory).

- [ ] **Step 5: Confirm capacity guard works**

Run: `python generate.py --count 999999`
Expected: `Error: requested 999999 images, but only <max> unique trait combinations are possible...` and non-zero exit, no partial files written beyond what a prior run left.

---

### Task 10: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write usage documentation**

`README.md`:
```markdown
# NFT Generator

Combine layered trait PNGs into a unique generative NFT collection with
weighted rarity and marketplace-ready metadata.

## Setup

```bash
pip install -r requirements.txt
```

## 1. Add your trait art

Put trait folders inside `layers/`, named `<order>_<TraitType>`
(e.g. `1_Background`, `2_Body`, `3_Eyes`, `4_Accessories`). The number
controls stacking order (lower = drawn first / at the back).

Inside each folder, name files `<Value>#<Weight>.png`
(e.g. `Blue#30.png`, `Gold#1.png`). Weight is relative — bigger number =
more common. A file named `None#<weight>.png` means "this trait can be
absent" (e.g. no accessory).

Try `python scripts/make_demo_assets.py` first to generate placeholder art
and see the folder structure in action before adding real artwork.

## 2. Edit config.json

Set your collection's `name`, `description`, and `symbol`.

## 3. Generate

```bash
python generate.py
```

You'll be asked how many NFTs to generate, then it will produce:
- `output/images/1.png`, `2.png`, ... — the composited images
- `output/metadata/1.json`, `2.json`, ... — matching trait metadata

Or skip the prompt: `python generate.py --count 1000`

If you ask for more images than the trait folders can produce unique
combinations of, it'll tell you the max and stop rather than generating
duplicates.

## Rarity report

After generation, a report prints showing how often each trait value
actually appeared, so you can confirm rare traits stayed rare.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add usage README"
```
