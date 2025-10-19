from flask import Flask, request
import random
import uuid

WEBHOOK_URL = ""
ACTIVE_TRANSACTIONS: list[str] = []

app = Flask(__name__)

@app.route("/transaction", methods = ['POST'])
def init_transaction():
    if request.is_json:
        data = request.json
        valor = data.get('valor')
        client_id = data.get('client_id')
        
        id = uuid.uuid4().hex
        
        ACTIVE_TRANSACTIONS.append(id)
        
        host_with_port = request.host
        return f"{host_with_port}/transaction/{id}"
    else:
        return "Request must be JSON", 400

@app.route("/transaction/<uuid:transaction_id>")
def pay_transaction(transaction_id: str):
    if not transaction_id in ACTIVE_TRANSACTIONS:
        return None
    
    ACTIVE_TRANSACTIONS.remove(transaction_id)
    
    status = random.choice([True, False])
    valor = random.randint()