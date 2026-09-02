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
