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
