
from pathlib import Path

from src.establishments import load_establishments
from src.geocoding_cache import GeocodingCache
from src.spatial_index import SpatialIndex


def build_spatial_index(
    csv_path: str | Path,
    cache: GeocodingCache,
    precision: int = 8,
) -> tuple[SpatialIndex, dict]:
    """Constrói o índice espacial usando apenas coordenadas em cache."""

    establishments = load_establishments(csv_path)
    index = SpatialIndex(precision=precision)

    indexed = 0
    missing_coordinates = 0
    not_found = 0

    for establishment in establishments:
        cached = cache.get(establishment["address"])

        if cached is None:
            missing_coordinates += 1
            continue

        if cached["status"] == "not_found":
            not_found += 1
            continue

        if cached["status"] != "found":
            missing_coordinates += 1
            continue

        record = dict(establishment)
        record["latitude"] = cached["latitude"]
        record["longitude"] = cached["longitude"]

        index.insert(record)
        indexed += 1

    summary = {
        "total_establishments": len(establishments),
        "indexed": indexed,
        "missing_coordinates": missing_coordinates,
        "not_found": not_found,
    }

    return index, summary
