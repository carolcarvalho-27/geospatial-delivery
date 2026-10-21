
import unittest

from src.trie import Trie


class TestTrie(unittest.TestCase):

    def setUp(self):
        self.trie = Trie()

    def test_insert_and_search_prefix(self):
        self.trie.insert("6gk1", "entregador-1")
        self.trie.insert("6gk2", "entregador-2")
        self.trie.insert("6gm3", "entregador-3")

        result = self.trie.search_prefix("6gk")
        self.assertCountEqual(
            result,
            ["entregador-1", "entregador-2"]
        )

    def test_prefix_ending_inside_compressed_edge(self):
        self.trie.insert("abcdef", "A")

        self.assertEqual(self.trie.search_prefix("abc"), ["A"])
        self.assertEqual(self.trie.search_prefix("abcd"), ["A"])

    def test_insert_key_that_is_prefix_of_another(self):
        self.trie.insert("geohash", "A")
        self.trie.insert("geo", "B")

        self.assertCountEqual(
            self.trie.search_prefix("geo"),
            ["A", "B"]
        )
        self.assertEqual(self.trie.search_prefix("geohash"), ["A"])

    def test_insert_keys_with_shared_prefix(self):
        self.trie.insert("abc", "A")
        self.trie.insert("abd", "B")
        self.trie.insert("axy", "C")

        self.assertCountEqual(
            self.trie.search_prefix("ab"),
            ["A", "B"]
        )

    def test_empty_prefix_returns_all_values(self):
        self.trie.insert("abc", "A")
        self.trie.insert("xyz", "B")

        self.assertCountEqual(
            self.trie.search_prefix(""),
            ["A", "B"]
        )

    def test_nonexistent_prefix(self):
        self.trie.insert("abcdef", "A")
        self.assertEqual(self.trie.search_prefix("xyz"), [])
        self.assertEqual(self.trie.search_prefix("abx"), [])

    def test_remove_value(self):
        self.trie.insert("abc", "A")
        self.trie.insert("abd", "B")

        self.assertTrue(self.trie.remove("abc", "A"))
        self.assertEqual(self.trie.search_prefix("abc"), [])
        self.assertEqual(self.trie.search_prefix("abd"), ["B"])

    def test_remove_missing_value(self):
        self.trie.insert("abc", "A")
        self.assertFalse(self.trie.remove("abc", "B"))
        self.assertEqual(self.trie.search_prefix("abc"), ["A"])

    def test_multiple_values_for_same_key(self):
        self.trie.insert("abc", "A")
        self.trie.insert("abc", "B")
        self.trie.insert("abc", "A")

        self.assertCountEqual(
            self.trie.search_prefix("abc"),
            ["A", "B"]
        )

        self.assertTrue(self.trie.remove("abc", "A"))
        self.assertEqual(self.trie.search_prefix("abc"), ["B"])

    def test_invalid_key(self):
        for key in ("", None, 123):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    self.trie.insert(key, "A")

    def test_invalid_prefix(self):
        with self.assertRaises(ValueError):
            self.trie.search_prefix(None)


if __name__ == "__main__":
    unittest.main()
