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
