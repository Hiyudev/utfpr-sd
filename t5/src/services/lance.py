import sys
import os
import grpc
from concurrent import futures
import datetime

# Adiciona o diretório raiz do projeto ao sys.path para importar 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from protocols.lance_pb2 import OnLanceRequest, OnLanceResponse, OnInitLeilaoRequest, OnInitLeilaoResponse, OnEndLeilaoResponse, OnEndLeilaoRequest
from protocols.lance_pb2_grpc import LanceServicer, add_LanceServicer_to_server

from protocols.pagamento_pb2 import OnWinnerRequest, OnWinnerResponse
from protocols.pagamento_pb2_grpc import PagamentoStub

from protocols.gateway_pb2 import OnLanceInvalidadoRequest, OnLanceInvalidadoResponse, OnLanceValidadoRequest, OnLanceValidadoResponse, OnLeilaoVencedorRequest, OnLeilaoVencedorResponse
from protocols.gateway_pb2_grpc import GatewayStub

channel = grpc.insecure_channel('localhost:50053')
pagamentoStub = PagamentoStub(channel)

channel = grpc.insecure_channel('localhost:50054')
gatewayStub = GatewayStub(channel)


# service Lance {
#    rpc Lance(LanceRequest) returns (LanceResponse) {}
#    rpc OnInitLeilao(OnInitLeilaoRequest) returns (OnInitLeilaoResponse) {}
#    rpc OnEndLeilao(OnEndLeilaoRequest) returns (OnEndLeilaoResponse) {}
#}

#message LanceRequest {
#    string leilao_id = 1;
#    string client_id = 2;
#    string value = 3;
#}
#
#message LanceResponse {
#    bool ok = 1;
#    string message = 2;
#}
#
#message OnInitLeilaoRequest {
#    string id = 1;
#    string description = 2;
#    float start = 3;
#    float end = 4;
#}
#
#message OnInitLeilaoResponse {
#    bool ok = 1;
#    string message = 2;
#}
#
#message OnEndLeilaoRequest {
#    string id = 1;
#}
#
#message OnEndLeilaoResponse {
#    bool ok = 1;
#    string message = 2;
#}

# Variáveis globais
leiloes: list[dict[str, str | datetime.datetime]] = []

class LanceServicer(LanceServicer):
    def OnLance(self, request: OnLanceRequest, _):
        # ...
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
                #message = serialize_dict(body)
                #channel_flask.basic_publish(
                #    exchange=EXCHANGE_NAME,
                #    body=message,
                #    routing_key="lance_validado",
                #)
                #print("[MS-Lance] Lance validado!")

                #TODO: chamar stub de gateway OnLanceValidado

                response_stub = gatewayStub.OnLanceInvalidado()
                return OnLanceResponse(ok=True, message="Lance Validado!")
            else:
                #message = serialize_dict(body)
                #channel_flask.basic_publish(
                #    exchange=EXCHANGE_NAME,
                #    body=message,
                #    routing_key="lance_invalidado",
                #)
                #print("[MS-Lance] Lance invalidado!")

                #TODO: chamar stub de gateway OnLanceInvalidado
                return OnLanceResponse(ok=False, message="Lance invalidado!")
        else:
            print("[MS-Lance] leilao nao existe!")

    #return jsonify("Comando inválido."), 400
        return OnLanceResponse(ok=False, message="Erro!")
        #return InitTransactionResponse(link="", location=request)
    def OnInitLeilao(self, request: OnInitLeilaoRequest, _):
        #if method.routing_key == "leilao_iniciado":
        #    # Somente aceitará o lance se: ID do leilão existir e se o leilão estiver ativo;
        #    leilao = deserialize_leilao(body)
        #    leilao["highest_bid"] = "0"
        #    leilao["winner"] = "ninguem"
        #    leiloes.append(leilao)
        #
        #    print("[MS-Lance] Leilao iniciado!")

        leilao = {}
        leilao["id"] = request.id
        leilao["description"] = request.description
        leilao["start"] = request.start
        leilao["end"] = request.end
        leilao["highest_bid"] = "0"
        leilao["winner"] = "ninguem"
        leiloes.append(leilao)

        print("[MS-Lance] Leilao iniciado!")

        return OnInitLeilaoResponse(ok=True, message="Sucesso em Lance")
    
    def OnEndLeilao(self, request: OnEndLeilaoRequest, _):
        #if method.routing_key == "leilao_finalizado":
            # Requisito 4.5 - Ao finalizar um leilão, deve publicar na fila leilao_vencedor,
            # informando o ID do leilão, o ID do vencedor do leilão e o valor
            # negociado. O vencedor é o que efetuou o maior lance válido até o
            # encerramento.

            leilao_id = request.id

            lance_vencedor = next(
                (d.get("highest_bid") for d in leiloes if leilao_id in d["id"]), None
            )

            cliente_vencedor = next(
                (d.get("winner") for d in leiloes if leilao_id in d["id"]), None
            )

            #message = serialize_dict(
            #    {
            #        "leilao_id": leilao_id,
            #        "lance_vencedor": lance_vencedor,
            #        "cliente_vencedor": cliente_vencedor,
            #    }
            #)
            # Remove o leilão finalizado da lista de leilões ativos
            leiloes.remove(next(d for d in leiloes if leilao_id in d["id"]))

            #channel.basic_publish(
            #    exchange=EXCHANGE_NAME, body=message, routing_key="leilao_vencedor"
            #)

            #TODO: chamar stub de gateway OnLeilaoVencedor
            #TODO: chamar stub de pagamento OnWinner
            print("[MS-Lance] Leilao finalizado!")

            return OnEndLeilaoResponse(ok=True, leilao_id = leilao_id, cliente_vencedor = cliente_vencedor, lance_vencedor = lance_vencedor)

    



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LanceServicer_to_server(LanceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("starting lance server...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
