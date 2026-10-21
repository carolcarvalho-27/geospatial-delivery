
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.geocoding import geocode_one
from src.geocoding_cache import GeocodingCache


class FakeLocation:
    latitude = -19.9167
    longitude = -43.9345


class TestGeocoding(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database = Path(self.temp_directory.name) / "cache.db"
        self.cache = GeocodingCache(database)

    def tearDown(self):
        self.temp_directory.cleanup()

    @patch("src.geocoding.Nominatim")
    def test_geocode_and_cache_result(self, mock_nominatim):
        mock_nominatim.return_value.geocode.return_value = FakeLocation()

        address = "Praça Sete, Belo Horizonte, MG, Brasil"

        result = geocode_one(address, self.cache)

        self.assertAlmostEqual(result["latitude"], -19.9167)
        self.assertAlmostEqual(result["longitude"], -43.9345)
        self.assertEqual(self.cache.get(address)["status"], "found")

    @patch("src.geocoding.Nominatim")
    def test_cached_result_avoids_new_request(self, mock_nominatim):
        address = "Praça Sete, Belo Horizonte, MG, Brasil"
        self.cache.save_found(address, -19.9167, -43.9345)

        result = geocode_one(address, self.cache)

        self.assertAlmostEqual(result["latitude"], -19.9167)
        mock_nominatim.assert_not_called()

    @patch("src.geocoding.Nominatim")
    def test_address_not_found(self, mock_nominatim):
        mock_nominatim.return_value.geocode.return_value = None

        result = geocode_one(
            "Endereço inexistente, Belo Horizonte, Brasil",
            self.cache,
        )

        self.assertIsNone(result)
        mock_nominatim.return_value.geocode.assert_called_once()


if __name__ == "__main__":
    unittest.main()
