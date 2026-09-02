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
