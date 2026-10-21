import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from approximate_index_builder import (
    build_approximate_spatial_index,
)


def main():
    csv_path = ROOT_DIR / "data" / "bares.csv"
    neighborhoods_path = (
        ROOT_DIR / "data" / "bairros" / "bh_neighborhood.json"
    )

    index, summary = build_approximate_spatial_index(
        csv_path=csv_path,
        neighborhoods_path=neighborhoods_path,
    )

    print("\n=== Resultado da construção do índice ===")
    print(f"Total de estabelecimentos: {summary['total_establishments']}")
    print(f"Associados a bairros: {summary['matched']}")
    print(f"Sem correspondência: {summary['unmatched']}")
    print(f"Registros indexados: {summary['indexed']}")

    print("\n=== Bairros sem correspondência ===")
    if summary["unmatched_neighborhoods"]:
        for neighborhood in summary["unmatched_neighborhoods"]:
            print(f"- {neighborhood}")
    else:
        print("Todos os bairros foram encontrados.")

    print(f"\nTamanho final do índice: {len(index)}")


if __name__ == "__main__":
    main()