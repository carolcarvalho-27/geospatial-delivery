
import json
import tempfile
import unittest
from pathlib import Path

from src.neighborhoods import (
    load_neighborhoods,
    normalize_neighborhood_name,
)


class TestNeighborhoods(unittest.TestCase):

    def test_normalize_neighborhood_name(self):
        self.assertEqual(
            normalize_neighborhood_name("  São João  "),
            "sao joao",
        )

    def test_load_neighborhoods(self):
        # Polígono de teste em coordenadas projetadas EPSG:31983.
        geometry = (
            "POLYGON (("
            "603000 7800000, "
            "604000 7800000, "
            "604000 7801000, "
            "603000 7801000, "
            "603000 7800000"
            "))"
        )

        data = {
            "fields": [
                {"id": "_id", "type": "int"},
                {"id": "NOME", "type": "text"},
                {"id": "GEOMETRIA", "type": "text"},
            ],
            "records": [
                [1, "Bairro de Teste", geometry],
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "neighborhoods.json"
            path.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            neighborhoods = load_neighborhoods(path)

        self.assertIn("bairro de teste", neighborhoods)

        neighborhood = neighborhoods["bairro de teste"]

        self.assertEqual(neighborhood["name"], "Bairro de Teste")
        self.assertGreater(
            neighborhood["latitude"], -20.5
        )
        self.assertLess(
            neighborhood["latitude"], -19.0
        )
        self.assertGreater(
            neighborhood["longitude"], -44.5
        )
        self.assertLess(
            neighborhood["longitude"], -43.0
        )


if __name__ == "__main__":
    unittest.main()
