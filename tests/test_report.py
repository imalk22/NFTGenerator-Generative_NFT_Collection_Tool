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
