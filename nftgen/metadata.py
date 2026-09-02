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
