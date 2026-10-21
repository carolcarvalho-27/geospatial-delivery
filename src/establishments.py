
import csv
import re
from pathlib import Path


REQUIRED_COLUMNS = {
    "_id",
    "DESC_LOGRADOURO",
    "NOME_LOGRADOURO",
    "NUMERO_IMOVEL",
    "NOME_BAIRRO",
    "NOME",
    "NOME_FANTASIA",
}


def normalize_text(value: str | None) -> str:
    """Remove espaços extras sem modificar o conteúdo original da base."""
    if value is None:
        return ""

    return re.sub(r"\s+", " ", value).strip()


def build_address(row: dict[str, str]) -> str:
    """Monta um endereço textual para geocodificação."""

    street_type = normalize_text(row.get("DESC_LOGRADOURO", ""))
    street_name = normalize_text(row.get("NOME_LOGRADOURO", ""))
    number = normalize_text(row.get("NUMERO_IMOVEL", ""))
    neighborhood = normalize_text(row.get("NOME_BAIRRO", ""))

    parts = []

    street = " ".join(part for part in (street_type, street_name) if part)
    if street:
        parts.append(street)

    if number:
        parts.append(number)

    if neighborhood:
        parts.append(neighborhood)

    parts.extend(["Belo Horizonte", "MG", "Brasil"])

    return ", ".join(parts)


def load_establishments(csv_path: str | Path) -> list[dict[str, str]]:
    """Carrega estabelecimentos e prepara os campos necessários."""

    path = Path(csv_path)

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("O CSV não possui cabeçalho.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}"
            )

        establishments = []

        for row in reader:
            establishment_id = normalize_text(row.get("_id"))

            if not establishment_id:
                continue

            name = (
                normalize_text(row.get("NOME_FANTASIA"))
                or normalize_text(row.get("NOME"))
            )

            establishments.append({
                "id": establishment_id,
                "name": name,
                "address": build_address(row),
                "street_type": normalize_text(row.get("DESC_LOGRADOURO")),
                "street": normalize_text(row.get("NOME_LOGRADOURO")),
                "number": normalize_text(row.get("NUMERO_IMOVEL")),
                "neighborhood": normalize_text(row.get("NOME_BAIRRO")),
            })

    return establishments
