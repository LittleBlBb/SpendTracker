from flask import Flask
from flask_restful import Api, Resource, reqparse
from DB_Working import get_transactions, delete_transaction, update_transaction, add_transaction

app = Flask(__name__)
api = Api()

transactions = get_transactions()

parser = reqparse.RequestParser()
parser.add_argument("category_id", type=int)
parser.add_argument("user_id", type=int)
parser.add_argument("product", type=str)
parser.add_argument("amount", type=float)
parser.add_argument("transaction_date", type=str)

class Main(Resource):
    def get(self, transaction_id):
        transactions = get_transactions()
        if transaction_id == 0:
            return transactions
            
        for tr in transactions:
            if tr["transaction_id"] == transaction_id:
                return tr
            
        return {"error": f"Transaction with ID: {transaction_id} not found"}, 404

    def delete(self, transaction_id):
        delete_transaction(transaction_id)
        transactions = get_transactions()
        return transactions

    def put(self, transaction_id):
        update_transaction(transaction_id, parser.parse_args())
        transactions = get_transactions()
        return transactions

class Transactions(Resource):
    def post(self):
        data = parser.parse_args()
        result = add_transaction(data)
        return result, 201

api.add_resource(Transactions, "/api/transactions")
api.add_resource(Main, "/api/transactions/<int:transaction_id>")
api.init_app(app)
if __name__ == "__main__":
    app.run(debug=True, port=3000, host="127.0.0.1")
