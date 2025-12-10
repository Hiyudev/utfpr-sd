from flask import Flask, request
import random
import uuid
import requests

# Variáveis globais
global_pagamento_url = "http://127.0.0.1:5000/webhook"
global_active_transactions: list[dict[str, any]] = []

app = Flask(__name__)


@app.route("/transaction", methods=["POST"])
def init_transaction():
    if request.is_json:
        data = request.json

        assert "value" in data
        assert "client_id" in data

        value = data.get("value")
        client_id = data.get("client_id")

        # Gera um identificador aleatorio para o pagamento
        id = uuid.uuid4().hex
        global_active_transactions.append(
            {"id": id, "client_id": client_id, "value": value}
        )
        print("[MS-Externo] Foi criado um novo link de pagamento.")

        return f"http://127.0.0.1:5555/transaction/{id}", 200
    else:
        return "A requisição sem corpo.", 400


@app.route("/transaction/<transaction_id>", methods=["GET"])
def pay_transaction(transaction_id: str):
    active_transaction_ids = list(map(lambda d: d["id"], global_active_transactions))

    if not transaction_id in active_transaction_ids:
        return "Transação não encontrado", 404

    reference: dict[str, any] = next(
        (d for d in global_active_transactions if d["id"] == transaction_id), None
    )

    assert "value" in reference
    assert "client_id" in reference

    value = reference.get("value")
    client_id = reference.get("client_id")
    status = random.choice([True, False])

    global_active_transactions.remove(reference)

    payload = {
        "value": value,
        "status": status,
        "transaction_id": transaction_id,
        "client_id": client_id,
    }

    try:
        response = requests.post(global_pagamento_url, json=payload)
        response.raise_for_status()

        print("[MS-Externo] Pagamento foi realizado.")

        return "Webhook enviado com sucesso!", 200
    except requests.exceptions.RequestException as e:
        return f"Erro ao enviar o webhook: {e}", 500


if __name__ == "__main__":
    app.run(port=5555)
