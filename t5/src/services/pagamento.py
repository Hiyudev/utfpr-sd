import functools
import os
import sys
import requests
import grpc
from concurrent import futures
from threading import Thread, Lock
from time import sleep
from flask import Flask, request, jsonify

# Adiciona o diretório raiz do projeto ao sys.path para importar 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))

from common.serial import deserialize_dict, serialize_dict

from utils.pagamento_pb2 import OnWinnerRequest, OnWinnerResponse
from utils.pagamento_pb2_grpc import PagamentoServicer, add_PagamentoServicer_to_server

from utils.gateway_pb2 import (
    OnLinkPagamentoRequest,
    OnLinkPagamentoResponse,
    OnStatusPagamentoRequest,
    OnStatusPagamentoResponse,
)
from utils.gateway_pb2_grpc import GatewayStub

channel = grpc.insecure_channel("localhost:50054")
gatewayStub = GatewayStub(channel)

app = Flask(__name__)

# Variáveis globais
global_externo_url = "http://127.0.0.1:5555/transaction"
global_transactions_mutex = None
global_transactions: list[dict[str, any]] = []


@app.route("/webhook", methods=["POST"])
def receive_webhook():
    if request.method == "POST":
        try:
            data = request.json

            assert "value" in data
            assert "status" in data
            assert "transaction_id" in data
            assert "client_id" in data

            global_transactions_mutex.acquire()
            global_transactions.append(data)
            global_transactions_mutex.release()

            print("[MS-Pagamento] Webhook recebido.")

            return jsonify("Webhook received successfully"), 200
        except Exception as e:
            return str(e), 400
    else:
        return jsonify("Method Not Allowed"), 405


class PagamentoServicer(PagamentoServicer):
    def OnWinner(self, request: OnWinnerRequest, _):
        payload = {
            "value": request.lance_vencedor,
            "client_id": request.cliente_vencedor,
        }

        try:
            response = requests.post(global_externo_url, json=payload)
            response.raise_for_status()

            link = response.text.replace("\n", "")

            try:
                response = gatewayStub.OnLinkPagamento(
                    OnLinkPagamentoRequest(
                        leilao_id=request.leilao_id,
                        lance_vencedor=request.lance_vencedor,
                        cliente_vencedor=request.cliente_vencedor,
                        link=link,
                    )
                )

                if not response.ok:
                    raise RuntimeError("...")

                print(
                    "[MS-Pagamento] Um link de pagamento foi criado e enviado link de pagamento."
                )
                return OnWinnerResponse(ok=True)
            except Exception as e:
                print(
                    "[MS-Pagamento] Algum problema no MS-Externo ou Gateway foi encontrado:",
                    e
                )
                return OnWinnerResponse(ok=False)
        except Exception as e:
            print(
                "[MS-Pagamento] Algum problema no MS-Externo ou Gateway foi encontrado:",
                e,
            )
            return OnWinnerResponse(ok=False)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_PagamentoServicer_to_server(PagamentoServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print("starting pagamento server...")
    server.wait_for_termination()


def checker():
    try:
        while True:
            sleep(0.2)  # Dorme por 200ms

            global_transactions_mutex.acquire()

            if len(global_transactions) == 0:
                global_transactions_mutex.release()
                continue

            for transaction in global_transactions:
                response = gatewayStub.OnStatusPagamento(
                    OnStatusPagamentoRequest(
                        value=str(transaction["value"]),
                        status=str(transaction["status"]),
                        transaction_id=transaction["transaction_id"],
                        client_id=transaction["client_id"],
                    )
                )

                if response.ok:
                    print(
                        "[MS-Pagamento] Enviado uma mensagem para 'status_pagamento'."
                    )

            global_transactions.clear()
            global_transactions_mutex.release()

    except KeyboardInterrupt:
        print("[MS-Pagamento] Exiting...")


def main_flask():
    app.run(port=5000)


if __name__ == "__main__":
    global_transactions_mutex = Lock()

    threads: list[Thread] = []
    threads.append(Thread(target=serve, daemon=True))
    threads.append(Thread(target=checker, daemon=True))

    for thread in threads:
        thread.start()

    main_flask()
