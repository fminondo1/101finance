from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
from bson.objectid import ObjectId
import requests

app = Flask('financiera101')
app.config['SECRET_KEY'] = 'hardcoded_secret_key_12345'  # Replace with a secure key in production

# Hardcoded Cosmos DB connection
client = MongoClient('mongodb+srv://fminondo:xyrreW-nisbi3-pahsuq@financieradb101.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000')
db = client['financiera101']

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email, permissions):
        self.id = id
        self.name = name
        self.email = email
        self.permissions = permissions

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(str(user_data['_id']), user_data['name'], user_data['email'], user_data['permissions'])
    return None

def get_exchange_rate():
    token = 'your_banxico_api_token'  # Replace with your actual Banxico token
    url = 'https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/oportuno'
    headers = {'Bmx-Token': token}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        rate = float(data['bmx']['series'][0]['datos'][0]['dato'])
        return f"{rate:.2f} MXN/USD"
    except:
        return "N/A"

@app.route('/')
def index():
    exchange_rate = get_exchange_rate()
    return render_template('index.html', exchange_rate=exchange_rate)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = db.users.find_one({'name': username})
        if user_data and check_password_hash(user_data['password'], password):
            user = User(str(user_data['_id']), user_data['name'], user_data['email'], user_data['permissions'])
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/configuration', methods=['GET', 'POST'])
@login_required
def configuration():
    if not current_user.permissions.get('configuration', False):
        flash('No permission')
        return redirect(url_for('index'))
    if request.method == 'POST':
        config_type = request.form['type']
        config_data = {
            'type': config_type,
            'interest_rate': float(request.form.get('interest_rate', 0)),
            'opening_commission': float(request.form.get('opening_commission', 0)),
            'max_term': int(request.form.get('max_term', 0))
        }
        if config_type == 'Arrendamiento':
            config_data['max_residual_value'] = float(request.form.get('max_residual_value', 0))
        elif config_type == 'Credito Hipotecario':
            config_data['annual_insurance'] = float(request.form.get('annual_insurance', 0))
        db.configuration.update_one({'type': config_type}, {'$set': config_data}, upsert=True)
        flash('Configuration saved')
    # Fetch all configurations with defaults if not found
    configs = {doc['type']: doc for doc in db.configuration.find()}
    default_config = {'interest_rate': 5.0, 'opening_commission': 2.0, 'max_term': 36}
    arrendamiento_config = configs.get('Arrendamiento', {**default_config, 'max_residual_value': 10.0})
    credito_simple_config = configs.get('Credito Simple', default_config)
    credito_hipotecario_config = configs.get('Credito Hipotecario', {**default_config, 'max_term': 20, 'annual_insurance': 1.0})
    return render_template('configuration.html', configs={
        'Arrendamiento': arrendamiento_config,
        'Credito Simple': credito_simple_config,
        'Credito Hipotecario': credito_hipotecario_config
    })

@app.route('/calculators/arrendamiento', methods=['GET', 'POST'])
@login_required
def calculators_arrendamiento():
    config = db.configuration.find_one({'type': 'Arrendamiento'}) or {'interest_rate': 5.0, 'opening_commission': 2.0}
    result = None
    if request.method == 'POST':
        contract_value = float(request.form['contract_value'])
        term = int(request.form['term'])
        monthly_rate = config['interest_rate'] / 100 / 12
        monthly_rent = (contract_value * monthly_rate) / (1 - (1 + monthly_rate) ** -term)
        opening_commission = contract_value * (config['opening_commission'] / 100)
        result = {
            'monthly_rent': "{:,.2f}".format(monthly_rent),
            'advance_rents': "{:,.2f}".format(monthly_rent * 2),
            'opening_commission': "{:,.2f}".format(opening_commission),
            'total_initial_payment': "{:,.2f}".format(monthly_rent * 2 + opening_commission)
        }
    return render_template('arrendamiento.html', result=result)

@app.route('/calculators/credito_simple', methods=['GET', 'POST'])
@login_required
def calculators_credito_simple():
    config = db.configuration.find_one({'type': 'Credito Simple'}) or {'interest_rate': 5.0, 'opening_commission': 2.0}
    result = None
    if request.method == 'POST':
        loan_amount = float(request.form['loan_amount'])
        term = int(request.form['term'])
        monthly_rate = config['interest_rate'] / 100 / 12
        monthly_payment = (loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -term)
        result = {'monthly_payment': "{:,.2f}".format(monthly_payment)}
    return render_template('credito_simple.html', result=result)

@app.route('/calculators/credito_hipotecario', methods=['GET', 'POST'])
@login_required
def calculators_credito_hipotecario():
    config = db.configuration.find_one({'type': 'Credito Hipotecario'}) or {'interest_rate': 5.0, 'opening_commission': 2.0, 'annual_insurance': 1.0}
    result = None
    if request.method == 'POST':
        loan_amount = float(request.form['loan_amount'])
        term_years = int(request.form['term'])
        term_months = term_years * 12
        monthly_rate = config['interest_rate'] / 100 / 12
        monthly_payment = (loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -term_months)
        monthly_insurance = (loan_amount * (config['annual_insurance'] / 100)) / 12
        total_monthly_payment = monthly_payment + monthly_insurance
        result = {'monthly_payment': "{:,.2f}".format(total_monthly_payment)}
    return render_template('credito_hipotecario.html', result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
