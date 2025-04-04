from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '823362fad9cfbad19cfd8e50467a937f'

# MongoDB Connection to Azure Cosmos DB
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")
try:
    client = pymongo.MongoClient(mongo_uri)
    db = client['101finance_db']
except pymongo.errors.ConnectionError as e:
    print(f'Failed to connect to Cosmos DB: {e}')

# Collections
users_collection = db['users']
settings_collection = db['settings']

# User Model
class User(UserMixin):
    def __init__(self, email, password_hash, role, id=None):
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.id = id

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': user_id})
    if user_data:
        return User(user_data['email'], user_data['password_hash'], user_data['role'], user_data['_id'])
    return None

# Fetch Exchange Rate (simulated for now)
def get_exchange_rate():
    # Simulated API call (replace with real API like Banco de México if needed)
    return {'date': datetime.now().strftime('%Y-%m-%d'), 'rate': 19.85}

# Main Route (Index)
@app.route('/', methods=['GET', 'POST'])
def index():
    exchange_rate = get_exchange_rate()
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        try:
            lease_amount = float(request.form.get('lease_amount', 0))
            residual_value = min(float(request.form.get('residual_value', 0)), 10.0)
            term = int(request.form.get('term', 12))
            return redirect(url_for('results', name=name, email=email, lease_amount=lease_amount, residual_value=residual_value, term=term))
        except ValueError:
            flash('Por favor, ingrese valores numéricos válidos', 'error')
    return render_template('index.html', exchange_rate=exchange_rate)

# Results Route
@app.route('/results')
def results():
    exchange_rate = get_exchange_rate()
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    try:
        lease_amount = float(request.args.get('lease_amount', 0))
        residual_value = float(request.args.get('residual_value', 0))
        term = int(request.args.get('term', 12))
    except ValueError:
        flash('Error en los datos enviados', 'error')
        return redirect(url_for('index'))

    try:
        settings_list = list(settings_collection.find())
        if not settings_list:
            settings = {'Interest Rate': 5.5, 'Comisión por Apertura': 200, 'Rentas por Anticipado': 1000}
        else:
            settings = {setting['name']: float(setting['value']) for setting in settings_list}
    except pymongo.errors.PyMongoError as e:
        flash(f'Error al conectar con la base de datos: {e}', 'error')
        settings = {'Interest Rate': 5.5, 'Comisión por Apertura': 200, 'Rentas por Anticipado': 1000}

    interest_rate = settings.get('Interest Rate', 5.5) / 100
    opening_fee = settings.get('Comisión por Apertura', 200)
    advance_rentals = settings.get('Rentas por Anticipado', 1000)
    residual_amount = lease_amount * (residual_value / 100)
    amortizable_amount = lease_amount - residual_amount
    monthly_rent = (amortizable_amount * (1 + interest_rate)) / term + advance_rentals / term
    initial_payment = opening_fee + advance_rentals

    return render_template('results.html', exchange_rate=exchange_rate, name=name, email=email, lease_amount=lease_amount,
                           residual_value=residual_value, term=term, monthly_rent=monthly_rent,
                           initial_payment=initial_payment, interest_rate=interest_rate * 100,
                           opening_fee=opening_fee, advance_rentals=advance_rentals)

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    exchange_rate = get_exchange_rate()
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        try:
            user_data = users_collection.find_one({'email': email})
            if user_data:
                user = User(user_data['email'], user_data['password_hash'], user_data['role'], user_data['_id'])
                if user.check_password(password):
                    login_user(user)
                    flash('Inicio de sesión exitoso', 'success')
                    return redirect(url_for('index'))
            flash('Correo o contraseña inválidos', 'error')
        except pymongo.errors.PyMongoError as e:
            flash(f'Error al conectar con la base de datos: {e}', 'error')
    return render_template('login.html', exchange_rate=exchange_rate)

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('index'))

# Admin Settings Route (Protected)
@app.route('/admin_settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    exchange_rate = get_exchange_rate()
    if current_user.role != 'admin':
        flash('Acceso denegado: Solo administradores pueden acceder a esta página', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_settings':
            try:
                for setting in settings_collection.find():
                    new_value = request.form.get(setting['name'], setting['value'])
                    settings_collection.update_one(
                        {'_id': setting['_id']},
                        {'$set': {'value': new_value}}
                    )
                flash('Configuraciones actualizadas exitosamente', 'success')
            except pymongo.errors.PyMongoError as e:
                flash(f'Error al actualizar configuraciones: {e}', 'error')
        elif action == 'add_user':
            new_email = request.form.get('new_email', '')
            new_password = request.form.get('new_password', '')
            new_role = request.form.get('new_role', 'user')
            if new_email and new_password:
                try:
                    if not users_collection.find_one({'email': new_email}):
                        users_collection.insert_one({
                            'email': new_email,
                            'password_hash': generate_password_hash(new_password),
                            'role': new_role
                        })
                        flash(f'Usuario {new_email} agregado exitosamente', 'success')
                    else:
                        flash('El correo ya está registrado', 'error')
                except pymongo.errors.PyMongoError as e:
                    flash(f'Error al agregar usuario: {e}', 'error')
            else:
                flash('Correo y contraseña son requeridos', 'error')

    try:
        settings = list(settings_collection.find())
        if not settings:
            default_settings = {'Interest Rate': '5.5', 'Comisión por Apertura': '200', 'Rentas por Anticipado': '1000'}
            for name, value in default_settings.items():
                settings_collection.insert_one({'name': name, 'value': value})
            settings = list(settings_collection.find())
        users = list(users_collection.find())
    except pymongo.errors.PyMongoError as e:
        flash(f'Error al cargar datos: {e}', 'error')
        settings = [{'name': 'Interest Rate', 'value': '5.5'}, {'name': 'Comisión por Apertura', 'value': '200'}, {'name': 'Rentas por Anticipado', 'value': '1000'}]
        users = [{'email': 'francisco@101grados.mx', 'role': 'admin'}]
    return render_template('admin_settings.html', exchange_rate=exchange_rate, settings=settings, users=users)

if __name__ == '__main__':
    app.run(debug=True)
