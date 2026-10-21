
import math


EARTH_RADIUS_METERS = 6_371_000


def haversine_distance(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """Calcula a distância entre duas coordenadas, em metros."""

    coordinates = (latitude1, longitude1, latitude2, longitude2)

    if not all(math.isfinite(value) for value in coordinates):
        raise ValueError("As coordenadas devem ser números finitos.")

    if not -90 <= latitude1 <= 90:
        raise ValueError("Latitude 1 inválida.")
    if not -90 <= latitude2 <= 90:
        raise ValueError("Latitude 2 inválida.")
    if not -180 <= longitude1 <= 180:
        raise ValueError("Longitude 1 inválida.")
    if not -180 <= longitude2 <= 180:
        raise ValueError("Longitude 2 inválida.")

    lat1 = math.radians(latitude1)
    lat2 = math.radians(latitude2)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(longitude2 - longitude1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    # Protege o cálculo contra pequenos erros de arredondamento.
    a = min(1.0, max(0.0, a))

    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(a))
