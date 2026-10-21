import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from approximate_index_builder import (
    build_approximate_spatial_index,
)


class TestApproximateIndexBuilder(unittest.TestCase):

    def test_build_index_from_neighborhoods(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_path = temp_path / "bares.csv"
            csv_path.write_text(
                "_id,CNAE_PRINCIPAL,DESCRICAO_CNAE_PRINCIPAL,"
                "DESC_LOGRADOURO,NOME_LOGRADOURO,NUMERO_IMOVEL,"
                "COMPLEMENTO,NOME_BAIRRO,NOME,NOME_FANTASIA\n"
                "1,5611201,Restaurantes,Rua,Teste,10,,"
                "Bairro Teste,Bar Um,Bar Um\n"
                "2,5611201,Restaurantes,Rua,Exemplo,20,,"
                "Bairro Inexistente,Bar Dois,Bar Dois\n",
                encoding="utf-8",
            )

            neighborhoods_path = temp_path / "neighborhoods.json"

            data = {
                "fields": [
                    {"id": "_id", "type": "int"},
                    {"id": "NOME", "type": "text"},
                    {"id": "GEOMETRIA", "type": "text"},
                ],
                "records": [
                    [
                        1,
                        "Bairro Teste",
                        (
                            "POLYGON (("
                            "603500 7800000, "
                            "603700 7800000, "
                            "603700 7800200, "
                            "603500 7800200, "
                            "603500 7800000"
                            "))"
                        ),
                    ]
                ],
            }

            neighborhoods_path.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            index, summary = build_approximate_spatial_index(
                csv_path,
                neighborhoods_path,
            )

        self.assertEqual(summary["total_establishments"], 2)
        self.assertEqual(summary["matched"], 1)
        self.assertEqual(summary["unmatched"], 1)
        self.assertEqual(summary["indexed"], 1)
        self.assertEqual(len(index), 1)
        self.assertEqual(
            summary["unmatched_neighborhoods"],
            ["Bairro Inexistente"],
        )


if __name__ == "__main__":
    unittest.main()
