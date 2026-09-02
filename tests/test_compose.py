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
