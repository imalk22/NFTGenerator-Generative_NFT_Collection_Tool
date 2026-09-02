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
