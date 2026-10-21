
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from src.geocoding_cache import GeocodingCache


class GeocodingError(Exception):
    """Erro ao consultar o serviço de geocodificação."""


def geocode_one(address: str, cache: GeocodingCache) -> dict | None:
    """Consulta um endereço individual e guarda o resultado no cache.

    Retorna latitude/longitude, None quando não há resultado
    ou lança GeocodingError quando a consulta falha.
    """

    address = address.strip()

    if not address:
        raise ValueError("O endereço não pode estar vazio.")

    cached = cache.get(address)

    if cached is not None:
        if cached["status"] == "not_found":
            return None

        return {
            "latitude": cached["latitude"],
            "longitude": cached["longitude"],
        }

    geolocator = Nominatim(
        user_agent="geospatial_delivery_academic_project"
    )

    try:
        location = geolocator.geocode(
            address,
            exactly_one=True,
            timeout=15,
            country_codes="br",
        )
    except (GeocoderServiceError, GeocoderTimedOut) as error:
        raise GeocodingError(
            "Não foi possível consultar o Nominatim. "
            "Verifique a conexão e tente novamente mais tarde."
        ) from error

    if location is None:
        cache.save_not_found(address)
        return None

    latitude = location.latitude
    longitude = location.longitude

    cache.save_found(address, latitude, longitude)

    return {
        "latitude": latitude,
        "longitude": longitude,
    }
