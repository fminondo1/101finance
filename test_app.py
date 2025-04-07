import pytest
from app import app, db, get_exchange_rate
from werkzeug.security import generate_password_hash

# Prueba de conexión a la base de datos
def test_database_connection():
    try:
        db.command('ping')
        assert True
    except Exception as e:
        assert False, f"Database connection failed: {e}"

# Prueba de autenticación de usuario
def test_user_authentication():
    with app.test_client() as client:
        # Crear un usuario de prueba
        hashed_password = generate_password_hash('testpassword')
        db.users.insert_one({
            'name': 'testuser',
            'email': 'test@example.com',
            'password': hashed_password,
            'permissions': {'configuration': False, 'catalog': False}
        })
        
        # Intentar iniciar sesión
        response = client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
        assert response.status_code == 302  # Redirección después del login exitoso

# Prueba del calculador de Arrendamiento
def test_arrendamiento_calculator():
    with app.test_client() as client:
        # Simular login
        client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
        
        # Enviar datos al calculador
        response = client.post('/calculators/arrendamiento', data={
            'contract_value': '100000',
            'term': '12'
        })
        assert b'Monthly Rent' in response.data  # Verificar que se muestre el resultado

# Prueba del calculador de Crédito Simple
def test_credito_simple_calculator():
    with app.test_client() as client:
        # Simular login
        client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
        
        # Enviar datos al calculador
        response = client.post('/calculators/credito_simple', data={
            'loan_amount': '50000',
            'term': '6'
        })
        assert b'Monthly Payment' in response.data  # Verificar que se muestre el resultado

# Prueba del calculador de Crédito Hipotecario
def test_credito_hipotecario_calculator():
    with app.test_client() as client:
        # Simular login
        client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
        
        # Enviar datos al calculador
        response = client.post('/calculators/credito_hipotecario', data={
            'loan_amount': '200000',
            'term': '10'
        })
        assert b'Monthly Payment' in response.data  # Verificar que se muestre el resultado

# Prueba de la función get_exchange_rate
def test_get_exchange_rate():
    rate = get_exchange_rate()
    assert isinstance(rate, str)
    assert 'MXN/USD' in rate or rate == 'N/A'
