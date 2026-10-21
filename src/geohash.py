
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
MAX_PRECISION = 8


def encode_geohash(latitude: float, longitude: float, precision: int = MAX_PRECISION) -> str:
    """Codifica latitude e longitude em um Geohash de até 8 caracteres."""

    if not -90 <= latitude <= 90:
        raise ValueError("A latitude deve estar entre -90 e 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("A longitude deve estar entre -180 e 180.")

    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError("A precisão deve ser um número inteiro.")

    if not 1 <= precision <= MAX_PRECISION:
        raise ValueError(f"A precisão deve estar entre 1 e {MAX_PRECISION}.")

    lat_min, lat_max = -90.0, 90.0
    lon_min, lon_max = -180.0, 180.0

    geohash = []
    bits = 0
    bit_count = 0
    use_longitude = True

    for _ in range(precision * 5):
        if use_longitude:
            midpoint = (lon_min + lon_max) / 2

            if longitude >= midpoint:
                bits = (bits << 1) | 1
                lon_min = midpoint
            else:
                bits = bits << 1
                lon_max = midpoint
        else:
            midpoint = (lat_min + lat_max) / 2

            if latitude >= midpoint:
                bits = (bits << 1) | 1
                lat_min = midpoint
            else:
                bits = bits << 1
                lat_max = midpoint

        bit_count += 1
        use_longitude = not use_longitude

        if bit_count == 5:
            geohash.append(BASE32[bits])
            bits = 0
            bit_count = 0

    return "".join(geohash)

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
MAX_PRECISION = 8


def encode_geohash(latitude: float, longitude: float, precision: int = MAX_PRECISION) -> str:
    """Codifica latitude e longitude em um Geohash de até 8 caracteres."""

    if not -90 <= latitude <= 90:
        raise ValueError("A latitude deve estar entre -90 e 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("A longitude deve estar entre -180 e 180.")

    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError("A precisão deve ser um número inteiro.")

    if not 1 <= precision <= MAX_PRECISION:
        raise ValueError(f"A precisão deve estar entre 1 e {MAX_PRECISION}.")

    lat_min, lat_max = -90.0, 90.0
    lon_min, lon_max = -180.0, 180.0

    geohash = []
    bits = 0
    bit_count = 0
    use_longitude = True

    for _ in range(precision * 5):
        if use_longitude:
            midpoint = (lon_min + lon_max) / 2

            if longitude >= midpoint:
                bits = (bits << 1) | 1
                lon_min = midpoint
            else:
                bits = bits << 1
                lon_max = midpoint
        else:
            midpoint = (lat_min + lat_max) / 2

            if latitude >= midpoint:
                bits = (bits << 1) | 1
                lat_min = midpoint
            else:
                bits = bits << 1
                lat_max = midpoint

        bit_count += 1
        use_longitude = not use_longitude

        if bit_count == 5:
            geohash.append(BASE32[bits])
            bits = 0
            bit_count = 0

    return "".join(geohash)
