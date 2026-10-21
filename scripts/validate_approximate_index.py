
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from approximate_index_builder import (
    build_approximate_spatial_index,
)


def main():
    index, summary = build_approximate_spatial_index(
        csv_path=ROOT_DIR / "data" / "bares.csv",
        neighborhoods_path=(
            ROOT_DIR / "data" / "bairros" / "bh_neighborhood.json"
        ),
    )

    assert len(index) == summary["indexed"]
    assert summary["matched"] + summary["unmatched"] == (
        summary["total_establishments"]
    )

    print("Integridade das contagens: OK")
    print(f"Registros no índice: {len(index)}")

    # Usa as coordenadas de um bairro conhecido para testar a busca.
    from neighborhoods import load_neighborhoods

    neighborhoods = load_neighborhoods(
        ROOT_DIR / "data" / "bairros" / "bh_neighborhood.json"
    )

    sample = neighborhoods.get("beira-linha")

    if sample is None:
        print("Bairro de referência não encontrado; busca não testada.")
        return

    results = index.search_radius(
        sample["latitude"],
        sample["longitude"],
        2000,
    )

    print(f"Resultados encontrados em até 2 km: {len(results)}")
    print("Busca por raio executada: OK")


if __name__ == "__main__":
    main()
