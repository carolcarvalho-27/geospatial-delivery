
import math

from geohash import encode_geohash
from geo_distance import haversine_distance
from trie import Trie


EARTH_RADIUS_METERS = 6_371_000
MAX_RADIUS_METERS = 2_000


class SpatialIndex:
    """Indexa estabelecimentos por Geohash usando uma Trie."""

    def __init__(self, precision: int = 8):
        if (
            not isinstance(precision, int)
            or isinstance(precision, bool)
            or not 1 <= precision <= 8
        ):
            raise ValueError("A precisão deve estar entre 1 e 8.")

        self.precision = precision
        self.trie = Trie()
        self._records = {}

    def insert(self, establishment: dict) -> None:
        """Insere um estabelecimento com coordenadas válidas."""
        if not isinstance(establishment, dict):
            raise ValueError("O estabelecimento deve ser um dicionário.")

        if "id" not in establishment:
            raise ValueError("O estabelecimento deve possuir um id.")

        latitude = establishment.get("latitude")
        longitude = establishment.get("longitude")

        if latitude is None or longitude is None:
            raise ValueError("O estabelecimento deve possuir coordenadas.")

        geohash = encode_geohash(
            latitude, longitude, self.precision
        )

        record = dict(establishment)
        record["geohash"] = geohash
        record_id = str(record["id"])

        if record_id in self._records:
            old_record = self._records[record_id]
            self.trie.remove(old_record["geohash"], old_record)

        self._records[record_id] = record
        self.trie.insert(geohash, record)

    def search_prefix(self, prefix: str) -> list[dict]:
        """Retorna registros cujos Geohashes começam pelo prefixo."""
        if not isinstance(prefix, str):
            raise ValueError("O prefixo deve ser uma string.")

        if not prefix:
            return []

        if len(prefix) > self.precision:
            raise ValueError("O prefixo excede a precisão do índice.")

        return self.trie.search_prefix(prefix)

    @staticmethod
    def _validate_coordinates(latitude, longitude):
        if (
            isinstance(latitude, bool)
            or isinstance(longitude, bool)
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
        ):
            raise ValueError("As coordenadas devem ser numéricas.")

        if not math.isfinite(latitude) or not math.isfinite(longitude):
            raise ValueError("As coordenadas devem ser finitas.")

        if not -90 <= latitude <= 90:
            raise ValueError("Latitude inválida.")

        if not -180 <= longitude <= 180:
            raise ValueError("Longitude inválida.")

    def _candidate_prefixes(
        self, latitude: float, longitude: float, radius_meters: float
    ) -> set[str]:
        """Calcula prefixos das células que cobrem a área de busca."""
        angular_radius = radius_meters / EARTH_RADIUS_METERS
        lat_delta = math.degrees(angular_radius)

        south = max(-90.0, latitude - lat_delta)
        north = min(90.0, latitude + lat_delta)

        # Próximo aos polos, a área pode abranger todas as longitudes.
        reaches_pole = south <= -90.0 or north >= 90.0

        if reaches_pole:
            west, east = -180.0, 180.0
        else:
            ratio = math.sin(angular_radius) / math.cos(
                math.radians(latitude)
            )
            lon_delta = math.degrees(
                math.asin(max(-1.0, min(1.0, ratio)))
            )
            west = longitude - lon_delta
            east = longitude + lon_delta

        # Escolhe uma precisão de busca que não seja excessivamente fina.
        search_precision = self.precision

        if radius_meters > 0:
            target_size = max(radius_meters * 2, 30.0)

            for precision in range(1, self.precision + 1):
                total_bits = precision * 5
                lon_bits = (total_bits + 1) // 2
                lat_bits = total_bits // 2

                lat_cell = 180.0 / (2 ** lat_bits)
                lon_cell = 360.0 / (2 ** lon_bits)

                approx_lat_size = lat_cell * 111_195
                approx_lon_size = (
                    lon_cell
                    * 111_195
                    * max(0.0, math.cos(math.radians(latitude)))
                )

                diagonal = math.hypot(
                    approx_lat_size, approx_lon_size
                )

                if diagonal <= target_size:
                    search_precision = precision
                    break

        # Limita o custo da enumeração de células, reduzindo a precisão
        # quando a área de busca cobre muitas células.
        while True:
            total_bits = search_precision * 5
            lon_bits = (total_bits + 1) // 2
            lat_bits = total_bits // 2

            lon_count = 2 ** lon_bits
            lat_count = 2 ** lat_bits
            lon_step = 360.0 / lon_count
            lat_step = 180.0 / lat_count

            y_min = max(
                0, min(lat_count - 1, int((south + 90) / lat_step))
            )
            y_max = max(
                0, min(lat_count - 1, int((north + 90) / lat_step))
            )

            if reaches_pole:
                x_ranges = [(0, lon_count - 1)]
            else:
                # Divide a faixa quando atravessa o antimeridiano.
                if west < -180:
                    intervals = [
                        (west + 360, 180),
                        (-180, east),
                    ]
                elif east > 180:
                    intervals = [
                        (west, 180),
                        (-180, east - 360),
                    ]
                else:
                    intervals = [(west, east)]

                x_ranges = []
                for left, right in intervals:
                    x_min = max(
                        0, min(lon_count - 1,
                               int((left + 180) / lon_step))
                    )
                    x_max = max(
                        0, min(lon_count - 1,
                               int((right + 180) / lon_step))
                    )
                    x_ranges.append((x_min, x_max))

            estimated_cells = sum(
                (x2 - x1 + 1) * (y_max - y_min + 1)
                for x1, x2 in x_ranges
            )

            if estimated_cells <= 5000 or search_precision == 1:
                break

            search_precision -= 1

        prefixes = set()

        for x_min, x_max in x_ranges:
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    cell_lat = -90 + (y + 0.5) * lat_step
                    cell_lon = -180 + (x + 0.5) * lon_step

                    prefix = encode_geohash(
                        cell_lat, cell_lon, search_precision
                    )
                    prefixes.add(prefix)

        return prefixes

    def search_radius(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
    ) -> list[dict]:
        """Busca estabelecimentos dentro do raio, em metros."""
        self._validate_coordinates(latitude, longitude)

        if (
            isinstance(radius_meters, bool)
            or not isinstance(radius_meters, (int, float))
            or not math.isfinite(radius_meters)
            or not 0 <= radius_meters <= MAX_RADIUS_METERS
        ):
            raise ValueError("O raio deve estar entre 0 e 2000 metros.")

        prefixes = self._candidate_prefixes(
            latitude, longitude, radius_meters
        )

        candidates = {}

        for prefix in prefixes:
            for record in self.search_prefix(prefix):
                candidates[str(record["id"])] = record

        results = []

        for record in candidates.values():
            distance = haversine_distance(
                latitude,
                longitude,
                record["latitude"],
                record["longitude"],
            )

            if distance <= radius_meters:
                result = dict(record)
                result["distance_meters"] = distance
                results.append(result)

        results.sort(key=lambda record: record["distance_meters"])
        return results

    def __len__(self) -> int:
        return len(self._records)
