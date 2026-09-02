# NFT Generator — Design Spec

Date: 2026-09-02

## Purpose

A Python command-line tool that composites layered trait PNGs (background,
body, eyes, accessories, etc.) into a large collection of unique generative
NFT images, with per-trait rarity weighting and standard marketplace
metadata output. This mirrors the technique used by production PFP
collection tooling (e.g. HashLips-style art engines), scaled down to a
single-user, single-machine script.

## Folder & naming convention

```
nft/
├── layers/
│   ├── 1_Background/
│   │   ├── Blue#30.png
│   │   ├── Red#10.png
│   │   └── Gold#1.png
│   ├── 2_Body/
│   │   └── ...
│   ├── 3_Eyes/
│   │   └── ...
│   └── 4_Accessories/
│       ├── None#50.png
│       └── Hat#10.png
├── output/
│   ├── images/     (1.png, 2.png, ...)
│   └── metadata/   (1.json, 2.json, ...)
├── config.json
├── generate.py
├── nftgen/
│   ├── __init__.py
│   ├── config.py       # load/validate config.json + CLI args
│   ├── traits.py        # scan layers/, parse folder+file names into trait pools
│   ├── compose.py       # weighted unique combination selection + image compositing
│   ├── metadata.py      # build + write ERC-721/OpenSea-style metadata JSON
│   └── report.py        # post-run rarity report
├── scripts/
│   └── make_demo_assets.py   # generates placeholder colored-shape PNGs into layers/
├── requirements.txt
└── README.md
```

- **Trait folder name** = `<order>_<TraitType>`. `<order>` is an integer
  controlling stacking order (lower draws first / at the bottom, higher
  draws last / on top). `<TraitType>` (with underscores replaced by spaces)
  becomes the `trait_type` in metadata attributes.
- **Trait file name** = `<Value>#<Weight>.png`. `<Value>` (underscores
  replaced by spaces) becomes the attribute `value`. `<Weight>` is a
  positive integer, relative to other weights in the same folder — weights
  do not need to sum to 100; the tool normalizes them into probabilities.
- A file whose `<Value>` is exactly `None` (case-insensitive) means "this
  trait is absent" for any NFT that rolls it: no image is composited for
  that layer, and the trait is omitted from that NFT's metadata
  `attributes` list. This lets optional traits (e.g. "no accessory") be
  legitimately and rarely/commonly absent, same as required traits.
- Only `.png` files are treated as trait assets; anything else in a trait
  folder (e.g. `.DS_Store`, notes) is ignored. A trait folder containing
  zero valid `.png` files is a fatal config error, naming the folder.
- A filename that doesn't match `<Value>#<Weight>.png` (missing `#`, or a
  non-integer / non-positive weight) is a fatal error, naming the exact
  file and the expected pattern.

## Config file (`config.json`)

```json
{
  "name": "My Collection",
  "description": "A collection of unique generated NFTs.",
  "symbol": "MYNFT",
  "layers_dir": "layers",
  "output_dir": "output",
  "start_edition": 1
}
```

All fields optional with sensible defaults (`layers_dir: "layers"`,
`output_dir: "output"`, `start_edition: 1`); `name`/`description`/`symbol`
default to placeholder strings if omitted, with a printed reminder to edit
them before using the collection for real.

## CLI

```
python generate.py                # prompts interactively for count
python generate.py --count 1000   # skips the prompt
python generate.py --config other_config.json
```

If `--count` is not given, the script prints
`How many NFTs do you want to generate?` and reads an integer from stdin.
Non-integer or non-positive input re-prompts with an error rather than
crashing.

Canvas size is auto-detected from the first (lowest-order) trait folder's
first image (by sorted filename), read once at startup.

## Generation algorithm

1. **Scan**: walk `layers_dir`, parse every subfolder into
   `(order, trait_type, [(value, weight, filepath_or_None), ...])`, sorted
   by `order` ascending, then by folder name ascending as a tie-break if
   two folders share the same `order`. Fatal error if `layers_dir` is
   missing or has no valid trait subfolders.
2. **Capacity check**: compute
   `max_unique = product(len(options) for each trait folder)`. If the
   requested count exceeds `max_unique`, stop immediately with an error
   stating the max achievable count — no partial run.
3. **Per-image loop**, `count` times:
   - Weighted-random pick one option per trait folder (Python's
     `random.choices` with the folder's normalized weights).
   - If this exact combination (tuple of chosen values, one per trait) has
     already been used, discard and re-roll (rejection sampling) until a
     new one is found. Given the capacity check in step 2, this always
     terminates.
   - Open each non-`None` chosen layer as RGBA; if its size doesn't match
     the detected canvas size, resize it to fit (Lanczos resample) and
     print a one-line warning naming the file — art is auto-corrected
     rather than the run failing on a mismatched source image.
   - Composite layers bottom-to-top via `Image.alpha_composite` onto a
     blank RGBA canvas of the detected size.
   - Save as `output/images/<edition>.png` where `edition` starts at
     `start_edition` and increments per image.
   - Build and write `output/metadata/<edition>.json` (see below).
   - Print progress (e.g. `Generated 340/1000`) at a fixed interval so
     large runs give feedback without flooding the terminal.
4. **Rarity report**: after all images are written, print a per-trait
   breakdown: each value's actual occurrence count and percentage across
   the run, so the user can confirm intended rarities held (e.g. "Gold: 1 /
   1000 = 0.1%"). Also print total unique combinations used vs. max
   possible.

## Metadata format

Per image, `output/metadata/<edition>.json`:

```json
{
  "name": "My Collection #1",
  "description": "A collection of unique generated NFTs.",
  "image": "1.png",
  "edition": 1,
  "attributes": [
    { "trait_type": "Background", "value": "Blue" },
    { "trait_type": "Body", "value": "Red" },
    { "trait_type": "Eyes", "value": "Green" }
  ]
}
```

`None`-valued traits for that edition are omitted from `attributes`
entirely (not included with value `"None"`), matching common marketplace
convention of only listing traits an NFT actually has.

## Demo assets

Because `layers/` starts empty, `scripts/make_demo_assets.py` generates a
small placeholder trait set (simple colored shapes drawn with Pillow, a
handful of values per folder with varied weights, including one
intentionally rare "legendary" value and one `None` option) into
`layers/`. This exists so the generator can be run and verified end-to-end
immediately, and to give a concrete naming-convention example the user can
delete and replace with real artwork. It is a one-time setup script, not
part of the generation pipeline.

## Error handling summary

- Missing/empty `layers_dir` → fatal, names the missing path.
- Trait folder with no valid `.png` files → fatal, names the folder.
- Malformed filename (no `#weight`) → fatal, names the file + expected
  pattern.
- Requested count > max unique combinations → fatal, states the max.
- Layer image size mismatch → non-fatal, auto-resize + warning.
- Interactive count prompt with bad input → re-prompt, not a crash.

## Dependencies

Pillow only (`requirements.txt`). No other third-party packages.

## Out of scope (YAGNI)

- No blockchain/minting integration (image + metadata generation only).
- No GUI — command-line only.
- No multi-collection / multi-config batch runs in one invocation.
- No image format besides PNG for source layers and output.
