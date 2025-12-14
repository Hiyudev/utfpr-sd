import sys
import os
import grpc
from concurrent import futures
import datetime

# Adiciona o diretório raiz do projeto ao sys.path para importar 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))

from utils.lance_pb2 import (
    OnLanceRequest,
    OnLanceResponse,
    OnInitLeilaoRequest,
    OnInitLeilaoResponse,
    OnEndLeilaoResponse,
    OnEndLeilaoRequest,
)
from utils.lance_pb2_grpc import LanceServicer, add_LanceServicer_to_server

from utils.pagamento_pb2 import OnWinnerRequest, OnWinnerResponse
from utils.pagamento_pb2_grpc import PagamentoStub

from utils.gateway_pb2 import (
    OnLanceInvalidadoRequest,
    OnLanceInvalidadoResponse,
    OnLanceValidadoRequest,
    OnLanceValidadoResponse,
    OnLeilaoVencedorRequest,
    OnLeilaoVencedorResponse,
)
from utils.gateway_pb2_grpc import GatewayStub

channel = grpc.insecure_channel("localhost:50053")
pagamentoStub = PagamentoStub(channel)

channel = grpc.insecure_channel("localhost:50054")
gatewayStub = GatewayStub(channel)


# service Lance {
#    rpc Lance(LanceRequest) returns (LanceResponse) {}
#    rpc OnInitLeilao(OnInitLeilaoRequest) returns (OnInitLeilaoResponse) {}
#    rpc OnEndLeilao(OnEndLeilaoRequest) returns (OnEndLeilaoResponse) {}
# }

# message LanceRequest {
#    string leilao_id = 1;
#    string client_id = 2;
#    string value = 3;
# }
#
# message LanceResponse {
#    bool ok = 1;
#    string message = 2;
# }
#
# message OnInitLeilaoRequest {
#    string id = 1;
#    string description = 2;
#    float start = 3;
#    float end = 4;
# }
#
# message OnInitLeilaoResponse {
#    bool ok = 1;
#    string message = 2;
# }
#
# message OnEndLeilaoRequest {
#    string id = 1;
# }
#
# message OnEndLeilaoResponse {
#    bool ok = 1;
#    string message = 2;
# }

# Variáveis globais
leiloes: list[dict[str, str | datetime.datetime]] = []


class LanceServicer(LanceServicer):
    def OnLance(self, request: OnLanceRequest, _):
        lance = request

        # checa se id do leilao existe em leiloes
        if any(lance.leilao_id in d["id"] for d in leiloes):
            print("[MS-Lance] leilao existe!")
            # checa se eh maior lance
            lance_vencedor = [
                d.get("highest_bid") for d in leiloes if lance.leilao_id in d["id"]
            ]

            if float(lance.value) > float(lance_vencedor[0]):
                # Requisito 4.4 - Se o lance for válido, o MS Lance publica o evento na fila lance_validado.
                [
                    d.update(highest_bid=lance.value)
                    for d in leiloes
                    if lance.leilao_id in d["id"]
                ]
                [
                    d.update(winner=lance.client_id)
                    for d in leiloes
                    if lance.leilao_id in d["id"]
                ]

                try:
                    response = gatewayStub.OnLanceValidado(
                        OnLanceValidadoRequest(
                            leilao_id=lance.leilao_id,
                            client_id=lance.client_id,
                            value=lance.value,
                        )
                    )

                    if not response.ok:
                        raise RuntimeError("...")

                    print("[MS-Lance] Lance validado!")
                    return OnLanceResponse(ok=True)
                except Exception as e:
                    print(f"[MS-Lance] Algum problema no Gateway foi encontrado: {e}")
                    return OnLanceResponse(ok=False)
            else:
                try:
                    response = gatewayStub.OnLanceInvalidado(
                        OnLanceInvalidadoRequest(
                            leilao_id=lance.leilao_id,
                            client_id=lance.client_id,
                            value=lance.value,
                        )
                    )

                    if not response.ok:
                        raise RuntimeError("...")

                    print("[MS-Lance] Lance invalidado!")
                    return OnLanceResponse(ok=True)
                except Exception as e:
                    print(f"[MS-Lance] Algum problema no Gateway foi encontrado: {e}")
                    return OnLanceResponse(ok=False)
        else:
            print("[MS-Lance] leilao nao existe!")

        return OnLanceResponse(ok=False)

    def OnInitLeilao(self, request: OnInitLeilaoRequest, _):
        leilao = {}
        leilao["id"] = request.id
        leilao["description"] = request.description
        leilao["start"] = request.start
        leilao["end"] = request.end
        leilao["highest_bid"] = "0"
        leilao["winner"] = "ninguem"
        leiloes.append(leilao)

        print("[MS-Lance] Leilao iniciado!")
        return OnInitLeilaoResponse(ok=True)

    def OnEndLeilao(self, request: OnEndLeilaoRequest, _):
        leilao_id = request.id

        lance_vencedor = next(
            (d.get("highest_bid") for d in leiloes if leilao_id in d["id"]), None
        )

        cliente_vencedor = next(
            (d.get("winner") for d in leiloes if leilao_id in d["id"]), None
        )

        # Remove o leilão finalizado da lista de leilões ativos
        leiloes.remove(next(d for d in leiloes if leilao_id in d["id"]))

        try:
            response_pagamento = pagamentoStub.OnWinner(
                OnWinnerRequest(
                    leilao_id=leilao_id,
                    cliente_vencedor=cliente_vencedor,
                    lance_vencedor=lance_vencedor,
                )
            )

            if not response_pagamento.ok:
                raise RuntimeError("...")
        except Exception as e:
            print("[MS-Lance] Algum problema no MS-Pagamento foi encontrado: ", e)

            return OnEndLeilaoResponse(
                ok=False,
                leilao_id=leilao_id,
                cliente_vencedor=cliente_vencedor,
                lance_vencedor=lance_vencedor,
            )

        try:
            response_gateway: OnLeilaoVencedorResponse = gatewayStub.OnLeilaoVencedor(
                OnLeilaoVencedorRequest(
                    lance_vencedor=lance_vencedor,
                    cliente_vencedor=cliente_vencedor,
                    leilao_id=leilao_id,
                )
            )

            if not response_gateway.ok:
                raise RuntimeError("...")
        except Exception as e:
            print("[MS-Lance] Algum problema no Gateway foi encontrado: ", e)

            return OnEndLeilaoResponse(
                ok=False,
                leilao_id=leilao_id,
                cliente_vencedor=cliente_vencedor,
                lance_vencedor=lance_vencedor,
            )

        print("[MS-Lance] Leilao finalizado!")
        return OnEndLeilaoResponse(
            ok=True,
            leilao_id=leilao_id,
            cliente_vencedor=cliente_vencedor,
            lance_vencedor=lance_vencedor,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_LanceServicer_to_server(LanceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("starting lance server...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
