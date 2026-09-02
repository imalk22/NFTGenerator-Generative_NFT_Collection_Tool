from typing import List, Tuple

from nftgen.traits import TraitFolder


def build_rarity_report(folders: List[TraitFolder], combos: List[Tuple[str, ...]]) -> dict:
    total = len(combos)
    report = {}

    for i, folder in enumerate(folders):
        value_counts = {opt.value: 0 for opt in folder.options}
        for combo in combos:
            value_counts[combo[i]] += 1

        report[folder.trait_type] = {
            value: {
                "count": count,
                "percent": round((count / total) * 100, 2) if total else 0.0,
            }
            for value, count in value_counts.items()
        }

    return report


def print_rarity_report(report: dict, total: int, max_unique: int) -> None:
    print("\n--- Rarity Report ---")
    for trait_type, values in report.items():
        print(f"\n{trait_type}:")
        for value, stats in sorted(values.items(), key=lambda kv: -kv[1]["count"]):
            print(f"  {value}: {stats['count']} / {total} ({stats['percent']}%)")
    print(f"\nUnique combinations used: {total} / {max_unique} possible")
