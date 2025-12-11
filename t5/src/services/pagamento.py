import functools
import os
import sys
import requests
import grpc
from concurrent import futures
from threading import Thread, Lock
from time import sleep
from flask import Flask, request, jsonify

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import deserialize_dict, serialize_dict

from protocols.pagamento_pb2 import OnWinnerRequest, OnWinnerResponse
from protocols.pagamento_pb2_grpc import PagamentoServicer, add_PagamentoServicer_to_server

from protocols.gateway_pb2 import OnLinkPagamentoRequest, OnLinkPagamentoResponse, OnStatusPagamentoRequest, OnStatusPagamentoResponse
from protocols.gateway_pb2_grpc import GatewayStub

channel = grpc.insecure_channel('localhost:50054')
gatewayStub = GatewayStub(channel)

app = Flask(__name__)

# Variáveis globais
# global_exchange_name = "exchange"
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


        data = deserialize_dict(body)

        assert "leilao_id" in data
        assert "lance_vencedor" in data
        assert "cliente_vencedor" in data

        payload = {
            "value": data["lance_vencedor"],
            "client_id": data["cliente_vencedor"],
        }

        try:
            response = requests.post(global_externo_url, json=payload)
            response.raise_for_status()

            link = response.text.replace("\n", "")

            print("[MS-Pagamento] Um link de pagamento foi criado.")

            body = data.copy()
            body["link"] = link
            #body = serialize_dict(body)

            # TODO: Chamar stub de gateway e enviar o link para la com OnLinkPagamento

            print("[MS-Pagamento] Enviado link de pagamento.")
            return OnWinnerResponse(ok= True, message= "[MS-Pagamento] Enviado link de pagamento.")
        except requests.exceptions.RequestException as e:
            print("[MS-Pagamento] Algum problema no MS-Externo foi encontrado.", e)
            return OnWinnerResponse(ok= False, message= "[MS-Pagamento] Algum problema no MS-Externo foi encontrado.")
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_PagamentoServicer_to_server(PagamentoServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print("starting pagamento server...")
    try:
        while True:
            sleep(0.2)  # Dorme por 200ms

            global_transactions_mutex.acquire()

            if len(global_transactions) == 0:
                global_transactions_mutex.release()
                continue

            for transaction in global_transactions:
                print("[MS-Pagamento] Enviado uma mensagem para 'status_pagamento'.")

                payload = serialize_dict(transaction)

                #TODO: chamar stub de gateway e enviar mensagem com OnStatusPagamento

                #channel_mutex.acquire()
                #channel.basic_publish(
                #    exchange=global_exchange_name,
                #    routing_key="status_pagamento",
                #   body=payload,
                #)
                #channel_mutex.release()

            global_transactions.clear()
            global_transactions_mutex.release()

    except KeyboardInterrupt:
        print("[MS-Pagamento] Exiting...")
    #server.wait_for_termination()


if __name__ == "__main__":
    global_transactions_mutex = Lock()
    serve()



