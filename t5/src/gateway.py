from threading import Thread, Lock
import uuid
import sys
import os
import requests
from concurrent import futures
import grpc
from flask import Blueprint, Flask, request, jsonify, session
from flask_sse import sse
from flask_cors import CORS

# Soluciona problemas relacionados a conflitos de tipos de threads
from gevent import monkey

monkey.patch_all()
import grpc.experimental.gevent as grpc_gevent

grpc_gevent.init_gevent()

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common' e 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "./utils")))

from common.serial import deserialize_dict, serialize_dict


from utils.gateway_pb2 import (
    OnLanceInvalidadoRequest,
    OnLanceInvalidadoResponse,
    OnLanceValidadoRequest,
    OnLanceValidadoResponse,
    OnLeilaoVencedorRequest,
    OnLeilaoVencedorResponse,
    OnLinkPagamentoRequest,
    OnLinkPagamentoResponse,
    OnStatusPagamentoRequest,
    OnStatusPagamentoResponse,
)
from utils.gateway_pb2_grpc import add_GatewayServicer_to_server, GatewayServicer as GatewayServicerTemplate

from utils.lance_pb2 import (
    OnLanceRequest,
    OnLanceResponse,
)
from utils.lance_pb2_grpc import LanceStub

from utils.leilao_pb2 import (
    GetLeiloesRequest,
    CreateLeilaoRequest,
    CreateLeilaoResponse,
)
from utils.leilao_pb2_grpc import LeilaoStub

app = Flask(__name__)
CORS(app)
app.secret_key = "DUTRA"
app.config["REDIS_URL"] = "redis://localhost"

sse_blueprint = Blueprint("sse_bp", __name__)
CORS(sse_blueprint)
sse_blueprint.register_blueprint(sse, url_prefix="/")

app.register_blueprint(sse_blueprint, url_prefix="/events")

global_ms_leilao_url = "http://127.0.0.1:8111/leilao"
global_ms_lance_url = "http://127.0.0.1:8100/lance"
global_interests: dict[str, list[str]] = {}
global_interests_mutex: Lock = None
EXCHANGE_NAME = "exchange"

channel = grpc.insecure_channel("localhost:50051")
lanceStub = LanceStub(channel)

channel = grpc.insecure_channel("localhost:50052")
leilaoStub = LeilaoStub(channel)


@app.route("/", methods=["GET"])
def index():
    return str(uuid.uuid4()), 200


@app.route("/handshake", methods=["GET"])
def route_handshake():
    sse.publish("Hello World!", type="handshake")
    return "", 200


@app.route("/leilao", methods=["GET", "POST"])
def route_leilao():
    # Requisito 3.1.2
    if request.method == "GET":
        try:
            # Checked
            leiloes_response = leilaoStub.GetLeiloes(GetLeiloesRequest())

            payload = []
            for leilao_instance in leiloes_response.leiloes:
                payload.append({
                    "id":leilao_instance.id,
                    "name":leilao_instance.name,
                    "description": leilao_instance.description,
                    "value": float(leilao_instance.value),
                    "start": leilao_instance.start,
                    "end": leilao_instance.end,
                })

            return jsonify(payload), 200
        except requests.exceptions.RequestException as e:
            return f"Erro na consulta dos leilões", 500
    # Requisito 3.1.1
    elif request.method == "POST":
        try:
            data = request.get_json()

            assert "name" in data
            assert "description" in data
            assert "value" in data
            assert "start" in data
            assert "end" in data
            
            assert isinstance(data["name"], str)
            assert isinstance(data["description"], str)
            assert isinstance(data["value"], float)
            assert isinstance(data["start"], int)
            assert isinstance(data["end"], int)

            response = leilaoStub.CreateLeilao(CreateLeilaoRequest(
                name=data["name"],
                description=data["description"],
                value=data["value"],
                start=data["start"],
                end=data["end"],
            ))
            
            if not response.ok:
                return f"Erro na criação do leilao", 500

            return "Leilao criado com sucesso", 201
        except requests.exceptions.RequestException as e:
            return f"Erro na criação do leilao: {e}", 500
    else:
        return "Method Not Allowed", 405


@app.route("/lance", methods=["POST"])
def route_lance():
    if request.method == "POST":
        try:
            body = request.get_json()

            assert "leilao_id" in body
            assert "client_id" in body
            assert "value" in body

            data = deserialize_dict(body)

            # response = requests.post(global_ms_lance_url, json=body)
            # response.raise_for_status()

            lanceRequest = OnLanceRequest(
                leilao_id=data["leilao_id"],
                client_id=data["client_id"],
                value=data["value"],
            )

            response: OnLanceResponse = lanceStub.OnLance(lanceRequest)

            print(response.message)

            return "Lance realizado", 201
        except requests.exceptions.RequestException as e:
            return f"Erro no lance: {e}", 500
    else:
        return "Method Not Allowed", 405


@app.route("/notificacoes/<leilao_id>", methods=["POST", "DELETE"])
def route_notificacoes(leilao_id: str):
    client_id = request.headers.get("Authorization", default="", type=str)

    if request.method == "POST":
        if len(client_id) == 0:
            return "Bad Request", 400

        global_interests_mutex.acquire()
        if client_id not in global_interests:
            global_interests[client_id] = []

        global_interests[client_id].append(leilao_id)
        global_interests_mutex.release()

        return "", 200
    elif request.method == "DELETE":
        if len(client_id) == 0:
            return "Bad Request", 400

        global_interests_mutex.acquire()
        if client_id not in global_interests:
            global_interests_mutex.release()
            return "Bad Request", 400

        if leilao_id not in global_interests[client_id]:
            global_interests_mutex.release()
            return "", 200

        global_interests[client_id].remove(leilao_id)
        global_interests_mutex.release()

        return "", 200
    else:
        return "Method Not Allowed", 405


class GatewayServicer(GatewayServicerTemplate):
    def OnLanceInvalidado(self, request: OnLanceInvalidadoRequest, _):

        data = {}

        data["leilao_id"] = request.leilao_id
        data["client_id"] = request.client_id
        data["value"] = request.value
        targeted_client_id = request.client_id

        with app.app_context():
            print(f"notification_{targeted_client_id}")
            payload = data.copy()
            payload["event_name"] = "lance invalidado"
            sse.publish(payload, type=f"notification_{targeted_client_id}")
        return OnLanceInvalidadoResponse(ok=True, message="Lance invalidado")

    def OnLanceValidado(self, request: OnLanceValidadoRequest, _):
        data = {}
        event_leilao_id = request.leilao_id

        data["leilao_id"] = request.leilao_id
        data["client_id"] = request.client_id
        data["value"] = request.value
        for client_id, leiloes in global_interests.items():
            if event_leilao_id not in leiloes:
                continue

            print("[API-Gateway] Enviado um evento SSE pelo leilão")

            with app.app_context():
                print(f"notification_{client_id}")
                payload = serialize_dict(data)
                payload["event_name"] = "lance validado"
                sse.publish(payload, type=f"notification_{client_id}")
        return OnLanceValidadoResponse(ok=True, message="Lance validado")

    def OnLeilaoVencedor(self, request: OnLeilaoVencedorRequest, _):

        data = {}
        event_leilao_id = request.leilao_id

        data["leilao_id"] = request.leilao_id
        data["lance_vencedor"] = request.lance_vencedor
        data["cliente_vencedor"] = request.cliente_vencedor
        for client_id, leiloes in global_interests.items():
            if event_leilao_id not in leiloes:
                continue

            print("[API-Gateway] Enviado um evento SSE pelo leilão")

            with app.app_context():
                print(f"notification_{client_id}")
                payload = serialize_dict(data)
                payload["event_name"] = "leilao vencedor"
                sse.publish(payload, type=f"notification_{client_id}")
        return OnLeilaoVencedorResponse(ok=True, message="leilao vencedor")

    def OnStatusPagamento(self, request: OnStatusPagamentoRequest, _):
        print("[API-Gateway] Enviado um evento SSE pelo usuário")

        data = {}

        data["value"] = request.value
        data["transaction_id"] = request.transaction_id
        data["status"] = request.status
        data["client_id"] = request.client_id

        targeted_client_id = request.client_id

        with app.app_context():
            print(f"notification_{targeted_client_id}")
            payload = data.copy()
            payload["event_name"] = "status pagamento"
            sse.publish(payload, type=f"notification_{targeted_client_id}")
        return OnStatusPagamentoResponse(ok=True, message="status pagamento")

    def OnLinkPagamento(self, request: OnLinkPagamentoRequest, _):
        data = {}

        data["leilao_id"] = request.leilao_id
        data["cliente_vencedor"] = request.cliente_vencedor
        data["lance_vencedor"] = request.lance_vencedor
        data["link"] = request.link
        targeted_client_id = request.client_id

        with app.app_context():
            print(f"notification_{targeted_client_id}")
            payload = data.copy()
            payload["event_name"] = "link pagamento"
            sse.publish(payload, type=f"notification_{targeted_client_id}")
        return OnLinkPagamentoResponse(ok=True, message="Link pagamento")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_GatewayServicer_to_server(GatewayServicer(), server)
    server.add_insecure_port("[::]:50054")

    server.start()
    print("starting gateway server...")
    server.wait_for_termination()


if __name__ == "gateway":
    global_interests_mutex = Lock()

    threads: list[Thread] = []
    threads.append(Thread(target=serve, daemon=True))

    for thread in threads:
        thread.start()
