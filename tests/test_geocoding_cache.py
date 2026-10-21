
import tempfile
import unittest
from pathlib import Path

from src.geocoding_cache import GeocodingCache


class TestGeocodingCache(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "cache.db"
        self.cache = GeocodingCache(database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_save_and_get_coordinates(self):
        address = "Rua Exemplo, 10, Belo Horizonte, MG, Brasil"

        self.cache.save_found(address, -19.9167, -43.9345)

        result = self.cache.get(address)

        self.assertEqual(result["status"], "found")
        self.assertAlmostEqual(result["latitude"], -19.9167)
        self.assertAlmostEqual(result["longitude"], -43.9345)

    def test_save_not_found(self):
        address = "Endereço inexistente"

        self.cache.save_not_found(address)

        result = self.cache.get(address)

        self.assertEqual(result["status"], "not_found")
        self.assertIsNone(result["latitude"])

    def test_unknown_address(self):
        self.assertIsNone(self.cache.get("Endereço não consultado"))

    def test_update_existing_address(self):
        address = "Rua Exemplo, 10"

        self.cache.save_not_found(address)
        self.cache.save_found(address, -19.9, -43.9)

        result = self.cache.get(address)

        self.assertEqual(result["status"], "found")
        self.assertEqual(self.cache.count(), 1)

    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            self.cache.save_found("Rua A", 95, -43)

        with self.assertRaises(ValueError):
            self.cache.save_found("Rua B", -19, 200)


if __name__ == "__main__":
    unittest.main()
