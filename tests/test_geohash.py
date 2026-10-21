
import unittest

from src.geohash import encode_geohash


class TestGeohash(unittest.TestCase):

    def test_known_coordinate(self):
        # Exemplo conhecido do formato Geohash padrão.
        self.assertEqual(
            encode_geohash(42.6, -5.6, precision=5),
            "ezs42"
        )

    def test_default_precision(self):
        result = encode_geohash(-19.9167, -43.9345)
        self.assertEqual(len(result), 8)

    def test_precision_limits(self):
        for precision in range(1, 9):
            result = encode_geohash(0, 0, precision)
            self.assertEqual(len(result), precision)

    def test_short_hash_is_prefix_of_long_hash(self):
        short = encode_geohash(-19.9167, -43.9345, precision=5)
        long = encode_geohash(-19.9167, -43.9345, precision=8)
        self.assertEqual(long[:5], short)

    def test_invalid_latitude(self):
        with self.assertRaises(ValueError):
            encode_geohash(91, 0)

    def test_invalid_longitude(self):
        with self.assertRaises(ValueError):
            encode_geohash(0, 181)

    def test_invalid_precision(self):
        for precision in (0, 9, -1, 2.5, True):
            with self.subTest(precision=precision):
                with self.assertRaises(ValueError):
                    encode_geohash(0, 0, precision)


if __name__ == "__main__":
    unittest.main()
