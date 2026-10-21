
import json
import unicodedata
from pathlib import Path

from pyproj import Transformer
from shapely import wkt


# Converte coordenadas projetadas de Belo Horizonte para latitude/longitude.
_TRANSFORMER = Transformer.from_crs(
    "EPSG:31983",
    "EPSG:4326",
    always_xy=True,
)


def normalize_neighborhood_name(name: str) -> str:
    """Normaliza nomes para facilitar a correspondência entre bases."""
    normalized = unicodedata.normalize("NFKD", name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(normalized.casefold().split())


def load_neighborhoods(
    json_path: str | Path,
) -> dict[str, dict[str, float | str]]:
    """
    Carrega os bairros de um JSON da PBH e calcula um ponto interno
    para cada geometria.

    Retorna um dicionário indexado pelo nome normalizado do bairro.
    Cada valor contém o nome original, a latitude e a longitude.
    """
    json_path = Path(json_path)

    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    fields = [field["id"] for field in data["fields"]]

    if "NOME" not in fields or "GEOMETRIA" not in fields:
        raise ValueError(
            "O JSON precisa conter os campos NOME e GEOMETRIA."
        )

    name_index = fields.index("NOME")
    geometry_index = fields.index("GEOMETRIA")

    neighborhoods = {}

    for record in data["records"]:
        name = record[name_index]
        geometry_wkt = record[geometry_index]

        if not name or not geometry_wkt:
            continue

        geometry = wkt.loads(geometry_wkt)

        if geometry.is_empty or not geometry.is_valid:
            continue

        # Garante que o ponto esteja dentro da geometria.
        point = geometry.representative_point()

        longitude, latitude = _TRANSFORMER.transform(
            point.x,
            point.y,
        )

        normalized_name = normalize_neighborhood_name(name)

        neighborhoods[normalized_name] = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
        }

    return neighborhoods
