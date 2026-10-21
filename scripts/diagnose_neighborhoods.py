
import sys
from pathlib import Path
from difflib import get_close_matches

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from neighborhoods import (
    load_neighborhoods,
    normalize_neighborhood_name,
)

NEIGHBORHOODS_PATH = (
    ROOT_DIR / "data" / "bairros" / "bh_neighborhood.json"
)

unmatched_names = [
    "BEIRA LINHA",
    "BONSUCESSO",
    "CAICARA ADELAIDE",
    "JARDIM LIBERDADE",
    "MORRO DOS MACACOS",
    "XODO MARIZE",
]


def main():
    neighborhoods = load_neighborhoods(NEIGHBORHOODS_PATH)
    known_names = list(neighborhoods.keys())

    for name in unmatched_names:
        normalized = normalize_neighborhood_name(name)

        matches = get_close_matches(
            normalized,
            known_names,
            n=5,
            cutoff=0.4,
        )

        print(f"\nNome não encontrado: {name}")

        if not matches:
            print("  Nenhum nome semelhante encontrado.")
            continue

        print("  Possíveis correspondências:")
        for match in matches:
            print(f"  - {neighborhoods[match]['name']}")


if __name__ == "__main__":
    main()
