
from pathlib import Path

from establishments import load_establishments
from neighborhoods import (
    load_neighborhoods,
    normalize_neighborhood_name,
)
from spatial_index import SpatialIndex



NEIGHBORHOOD_ALIASES = {
    "beira linha": "beira-linha",
    "bonsucesso": "conjunto bonsucesso",
    "caicara adelaide": "caicara-adelaide",
    "xodo marize": "xodo-marize",
}


def build_approximate_spatial_index(
    csv_path: str | Path,
    neighborhoods_path: str | Path,
    precision: int = 8,
) -> tuple[SpatialIndex, dict]:
    """
    Constrói um índice espacial usando pontos representativos
    dos bairros dos estabelecimentos.

    Não utiliza geocodificação individual dos endereços.
    """
    establishments = load_establishments(csv_path)
    neighborhoods = load_neighborhoods(neighborhoods_path)

    index = SpatialIndex(precision=precision)

    matched = 0
    unmatched = 0
    unmatched_neighborhoods = set()

    for establishment in establishments:

        neighborhood_name = normalize_neighborhood_name(
            establishment["neighborhood"]
        )

        canonical_name = NEIGHBORHOOD_ALIASES.get(
            neighborhood_name,
            neighborhood_name,
        )

        neighborhood = neighborhoods.get(canonical_name)

        if neighborhood is None:
            unmatched += 1
            unmatched_neighborhoods.add(
                establishment["neighborhood"]
            )
            continue

        record = {
            **establishment,
            "latitude": neighborhood["latitude"],
            "longitude": neighborhood["longitude"],
        }

        index.insert(record)
        matched += 1

    summary = {
        "total_establishments": len(establishments),
        "matched": matched,
        "unmatched": unmatched,
        "indexed": len(index),
        "unmatched_neighborhoods": sorted(
            unmatched_neighborhoods
        ),
    }

    return index, summary
