
import unittest

from src.spatial_index import SpatialIndex


def test_insert_and_search():
    index = SpatialIndex(precision=8)

    establishment = {
        "id": "1",
        "name": "Estabelecimento de teste",
        "latitude": -19.9191023,
        "longitude": -43.9385851,
    }

    index.insert(establishment)

    assert len(index) == 1

    geohash = establishment.copy()
    from src.geohash import encode_geohash

    prefix = encode_geohash(
        establishment["latitude"],
        establishment["longitude"],
        5,
    )

    results = index.search_prefix(prefix)

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["geohash"].startswith(prefix)


def test_duplicate_id_replaces_record():
    index = SpatialIndex()

    index.insert({
        "id": "1",
        "latitude": -19.9191,
        "longitude": -43.9385,
    })

    index.insert({
        "id": "1",
        "latitude": -19.9200,
        "longitude": -43.9400,
    })

    assert len(index) == 1


def test_invalid_precision(self):
    with self.assertRaises(ValueError):
        SpatialIndex(precision=9)


def test_missing_coordinates(self):
    index = SpatialIndex()

    with self.assertRaises(ValueError):
        index.insert({"id": "1"})


    def test_search_radius_includes_nearby_records(self):
        index = SpatialIndex()

        index.insert({
            "id": "near",
            "latitude": -19.9191,
            "longitude": -43.9385,
        })
        index.insert({
            "id": "far",
            "latitude": -19.95,
            "longitude": -43.98,
        })

        results = index.search_radius(
            -19.9191, -43.9385, 500
        )

        ids = [record["id"] for record in results]
        self.assertIn("near", ids)
        self.assertNotIn("far", ids)

    def test_search_radius_returns_distance(self):
        index = SpatialIndex()
        index.insert({
            "id": "origin",
            "latitude": -19.9191,
            "longitude": -43.9385,
        })

        results = index.search_radius(
            -19.9191, -43.9385, 100
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["distance_meters"], 0.0)

    def test_radius_cannot_exceed_2000_meters(self):
        index = SpatialIndex()

        with self.assertRaises(ValueError):
            index.search_radius(-19.9, -43.9, 2001)


    def test_search_across_geohash_cell_boundary(self):
        from src.geohash import encode_geohash

        index = SpatialIndex(precision=8)

        latitude = -19.9191
        longitude = -43.9385
        nearby_longitude = longitude + 0.002

        # Os pontos devem estar em células diferentes
        # na precisão 7, mas a distância é inferior a 500 m.
        self.assertNotEqual(
            encode_geohash(latitude, longitude, 7),
            encode_geohash(latitude, nearby_longitude, 7),
        )

        index.insert({
            "id": "nearby",
            "latitude": latitude,
            "longitude": nearby_longitude,
        })

        results = index.search_radius(
            latitude, longitude, 500
        )

        self.assertIn("nearby", [r["id"] for r in results])

    def test_search_across_antimeridian(self):
        index = SpatialIndex(precision=8)

        index.insert({
            "id": "across",
            "latitude": 0.0,
            "longitude": -179.999,
        })

        results = index.search_radius(
            0.0, 179.999, 500
        )

        self.assertIn("across", [r["id"] for r in results])
