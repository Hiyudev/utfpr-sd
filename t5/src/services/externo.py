import sys
import os
import grpc
from concurrent import futures

# Adiciona o diretório raiz do projeto ao sys.path para importar 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))

from externo_pb2 import InitTransactionRequest, InitTransactionResponse
from externo_pb2_grpc import ExternoServicer, add_ExternoServicer_to_server


class ExternoServicer(ExternoServicer):
    def InitTransaction(self, request: InitTransactionRequest, _):
        # ...
        return InitTransactionResponse(link="", location=request)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_ExternoServicer_to_server(ExternoServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
