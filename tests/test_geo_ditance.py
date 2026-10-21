import unittest

from src.geo_distance import haversine_distance


class TestHaversineDistance(unittest.TestCase):

    def test_same_coordinates(self):
        distance = haversine_distance(
            -19.9191, -43.9385,
            -19.9191, -43.9385,
        )
        self.assertEqual(distance, 0.0)

    def test_known_distance(self):
        # Aproximadamente 111,2 km entre estas latitudes.
        distance = haversine_distance(0, 0, 1, 0)
        self.assertAlmostEqual(distance, 111_195, delta=200)

    def test_invalid_latitude(self):
        with self.assertRaises(ValueError):
            haversine_distance(91, 0, 0, 0)

    def test_invalid_longitude(self):
        with self.assertRaises(ValueError):
            haversine_distance(0, 181, 0, 0)

    def test_non_finite_coordinates(self):
        with self.assertRaises(ValueError):
            haversine_distance(float("nan"), 0, 0, 0)


if __name__ == "__main__":
    unittest.main()