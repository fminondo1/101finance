from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient('mongodb+srv://fminondo:xyrreW-nisbi3-pahsuq@financieradb101.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000')
db = client['financiera101']

# Create admin user
admin_password = generate_password_hash('12345678')
db.users.drop()  # Reset for demo purposes
db.users.insert_one({
    'name': 'minondo',
    'email': 'admin@example.com',
    'password': admin_password,
    'permissions': {'configuration': True, 'catalog': True}
})
print('Admin user created')
