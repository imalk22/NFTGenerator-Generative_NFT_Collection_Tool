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
