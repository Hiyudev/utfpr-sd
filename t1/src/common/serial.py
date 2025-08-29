import json
from datetime import datetime


def serialize_leilao(leilao: dict[str, str | datetime]) -> bytes:
    # Verifica se as chaves existem
    assert "id" in leilao, "Key 'id' does not exist in the dictionary."
    assert (
        "description" in leilao
    ), "Key 'description' does not exist in the dictionary."
    assert "start" in leilao, "Key 'start' does not exist in the dictionary."
    assert "end" in leilao, "Key 'end' does not exist in the dictionary."

    # Verifica os tipos
    assert isinstance(leilao["id"], str), "Key 'id' must be a string."
    assert isinstance(leilao["description"], str), "Key 'description' must be a string."
    assert isinstance(leilao["start"], datetime), "Key 'start' must be a datetime."
    assert isinstance(leilao["end"], datetime), "Key 'end' must be a datetime."

    el = leilao.copy()

    # Converte datetime.datetime para número
    el["start"] = el["start"].timestamp()
    el["end"] = el["end"].timestamp()

    # Serializa um JSON para uma lista de bytes
    serialized = json.dumps(el).encode("utf-8")
    return serialized


def deserialize_leilao(leilao: bytes) -> dict[str, str | datetime]:
    # Verifica se as chaves existem
    assert "id" in leilao, "Key 'id' does not exist in the dictionary."
    assert (
        "description" in leilao
    ), "Key 'description' does not exist in the dictionary."
    assert "start" in leilao, "Key 'start' does not exist in the dictionary."
    assert "end" in leilao, "Key 'end' does not exist in the dictionary."

    # Verifica os tipos
    assert isinstance(leilao["id"], str), "Key 'id' must be a string."
    assert isinstance(leilao["description"], str), "Key 'description' must be a string."
    assert isinstance(leilao["start"], float), "Key 'start' must be a float."
    assert isinstance(leilao["end"], float), "Key 'end' must be a float."

    dict_el = json.loads(leilao.decode("utf-8"))

    # Converte número para datetime.datetime
    dict_el["start"] = datetime.fromtimestamp(dict_el["start"])
    dict_el["end"] = datetime.fromtimestamp(dict_el["end"])
    return dict_el
