
import tempfile
import unittest
from pathlib import Path

from src.establishments import load_establishments
from src.geocoding_cache import GeocodingCache
from src.index_builder import build_spatial_index


class TestIndexBuilder(unittest.TestCase):
    def test_build_index_using_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "bares.csv"
            cache_path = temp_path / "geocoding.db"

            csv_path.write_text(
                "_id,CNAE_PRINCIPAL,DESCRICAO_CNAE_PRINCIPAL,"
                "DESC_LOGRADOURO,NOME_LOGRADOURO,NUMERO_IMOVEL,"
                "COMPLEMENTO,NOME_BAIRRO,NOME,NOME_FANTASIA\n"
                '1,123,Teste,Rua,Exemplo,10,,Centro,Bar A,Bar A\n'
                '2,123,Teste,Rua,Outro,20,,Centro,Bar B,Bar B\n',
                encoding="utf-8",
            )

            establishments = load_establishments(csv_path)
            cache = GeocodingCache(str(cache_path))

            first_address = establishments[0]["address"]
            cache.save_found(first_address, -19.9191, -43.9385)
            cache.save_not_found(establishments[1]["address"])

            index, summary = build_spatial_index(csv_path, cache)

            self.assertEqual(len(index), 1)
            self.assertEqual(summary["total_establishments"], 2)
            self.assertEqual(summary["indexed"], 1)
            self.assertEqual(summary["missing_coordinates"], 0)
            self.assertEqual(summary["not_found"], 1)


if __name__ == "__main__":
    unittest.main()
