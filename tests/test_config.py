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
