import requests

print("\n=============GET=============")
res_get = requests.get("http://127.0.0.1:3000/api/transactions/4")
print(res_get.json())

print("\n=============DEL=============")
res_del = requests.delete("http://127.0.0.1:3000/api/transactions/18")
print(res_del.json())

print("\n=============PUT=============")
res_put = requests.put("http://127.0.0.1:3000/api/transactions/4", json= {"category_name": "Топливо", "amount": 1400, "product": "Бензин", "transaction_date": "24-12-2024"})
print(res_put.json())

print("\n=============POST=============")
res_post = requests.post("http://127.0.0.1:3000/api/transactions", json= {"user_id": 430103290, "category_id": 2, "amount": 1400, "product": "Бензин", "transaction_date": "24-12-2024"})
print(res_post.json())