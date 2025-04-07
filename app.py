from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')

# Conexión a la base de datos usando variable de entorno
mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    raise ValueError("No se encontró la variable de entorno MONGO_URI")
client = MongoClient(mongo_uri)
db = client['financiera101']

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Clase de usuario
class User(UserMixin):
    def __init__(self, username, permissions):
        self.id = username
        self.permissions = permissions

@login_manager.user_loader
def load_user(username):
    user_data = db.users.find_one({'name': username})
    if user_data:
        return User(username, user_data['permissions'])
    return None

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = db.users.find_one({'name': username})
        if user and user['password'] == request.form['password']:  # Simplificado, usa hash en producción
            login_user(User(username, user['permissions']))
            return redirect(url_for('index'))
        flash('Credenciales inválidas')
    return render_template('login.html')

# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Rutas de calculadoras (accesibles sin autenticación)
@app.route('/calculators/arrendamiento', methods=['GET', 'POST'])
def calculators_arrendamiento():
    if request.method == 'POST':
        # Lógica de la calculadora de arrendamiento aquí
        pass
    return render_template('arrendamiento.html')

@app.route('/calculators/credito_simple', methods=['GET', 'POST'])
def calculators_credito_simple():
    if request.method == 'POST':
        # Lógica de la calculadora de crédito simple aquí
        pass
    return render_template('credito_simple.html')

@app.route('/calculators/credito_hipotecario', methods=['GET', 'POST'])
def calculators_credito_hipotecario():
    if request.method == 'POST']:
        # Lógica de la calculadora de crédito hipotecario aquí
        pass
    return render_template('credito_hipotecario.html')

# Ruta de configuración (requiere autenticación)
@app.route('/configuration', methods=['GET', 'POST'])
@login_required
def configuration():
    if not current_user.permissions.get('configuration', False):
        flash('No tienes permiso para acceder a esta sección')
        return redirect(url_for('index'))
    # Lógica de configuración aquí
    return render_template('configuration.html')

# Ruta de usuarios (requiere autenticación)
@app.route('/users')
@login_required
def users():
    if not current_user.permissions.get('catalog', False):
        flash('No tienes permiso para acceder a esta sección')
        return redirect(url_for('index'))
    # Lógica de usuarios aquí
    return render_template('users.html')

if __name__ == '__main__':
    app.run(debug=True)
