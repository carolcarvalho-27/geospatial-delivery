
import csv
import tempfile
import unittest
from pathlib import Path

from src.establishments import load_establishments, normalize_text


class TestEstablishments(unittest.TestCase):

    def test_normalize_text(self):
        self.assertEqual(
            normalize_text("  RUA   EXEMPLO  "),
            "RUA EXEMPLO"
        )
        self.assertEqual(normalize_text(None), "")

    def test_load_csv(self):
        columns = [
            "_id",
            "DESC_LOGRADOURO",
            "NOME_LOGRADOURO",
            "NUMERO_IMOVEL",
            "NOME_BAIRRO",
            "NOME",
            "NOME_FANTASIA",
        ]

        row = {
            "_id": "123",
            "DESC_LOGRADOURO": "RUA",
            "NOME_LOGRADOURO": "EXEMPLO",
            "NUMERO_IMOVEL": "45",
            "NOME_BAIRRO": "CENTRO",
            "NOME": "EMPRESA EXEMPLO",
            "NOME_FANTASIA": "BAR EXEMPLO",
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bares.csv"

            with path.open(
                "w", encoding="utf-8", newline=""
            ) as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerow(row)

            establishments = load_establishments(path)

        self.assertEqual(len(establishments), 1)
        self.assertEqual(establishments[0]["id"], "123")
        self.assertEqual(establishments[0]["name"], "BAR EXEMPLO")
        self.assertIn("EXEMPLO", establishments[0]["address"])
        self.assertIn("CENTRO", establishments[0]["address"])
        self.assertIn("Belo Horizonte", establishments[0]["address"])

    def test_fallback_to_registered_name(self):
        columns = [
            "_id",
            "DESC_LOGRADOURO",
            "NOME_LOGRADOURO",
            "NUMERO_IMOVEL",
            "NOME_BAIRRO",
            "NOME",
            "NOME_FANTASIA",
        ]

        row = {
            "_id": "456",
            "DESC_LOGRADOURO": "AVE",
            "NOME_LOGRADOURO": "AFONSO PENA",
            "NUMERO_IMOVEL": "100",
            "NOME_BAIRRO": "CENTRO",
            "NOME": "EMPRESA CADASTRADA",
            "NOME_FANTASIA": "",
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bares.csv"

            with path.open(
                "w", encoding="utf-8", newline=""
            ) as file:
                writer = csv.DictWriter(file, fieldnames=columns)
                writer.writeheader()
                writer.writerow(row)

            establishments = load_establishments(path)

        self.assertEqual(
            establishments[0]["name"],
            "EMPRESA CADASTRADA"
        )

    def test_missing_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.csv"
            path.write_text("_id,NOME\n1,Teste\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_establishments(path)


if __name__ == "__main__":
    unittest.main()
