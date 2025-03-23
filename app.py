from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import math
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelos de la base de datos
from models import Cliente, Asesor

# Crear la base de datos
with app.app_context():
    db.create_all()

# Lista estática de asesores
asesores = [
    {"nombre": "Juan Pérez", "telefono": "555-1234", "email": "juan@empresa.com"},
    {"nombre": "María López", "telefono": "555-5678", "email": "maria@empresa.com"}
]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Datos del formulario
        valor_arrendamiento = float(request.form['valor_arrendamiento'])
        tasa_anual = float(request.form['tasa_anual']) / 100
        plazo_meses = int(request.form['plazo_meses'])
        valor_residual_porcentaje = float(request.form['valor_residual']) / 100
        comision_apertura_porcentaje = float(request.form['comision_apertura']) / 100
        rentas_anticipadas = int(request.form['rentas_anticipadas'])
        nombre_cliente = request.form['nombre_cliente']
        email_cliente = request.form['email_cliente']

        # Cálculos
        iva = 0.16
        valor_con_iva = valor_arrendamiento * (1 + iva)
        valor_residual = valor_arrendamiento * valor_residual_porcentaje
        tasa_mensual = (1 + tasa_anual) ** (1/12) - 1
        monto_a_financiar = valor_con_iva - valor_residual
        comision_apertura = valor_con_iva * comision_apertura_porcentaje

        renta_mensual_sin_iva = (monto_a_financiar * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo_meses))
        rentas_anticipadas_mxn = renta_mensual_sin_iva * rentas_anticipadas
        monto_ajustado = monto_a_financiar - rentas_anticipadas_mxn
        renta_mensual_final = (monto_ajustado * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo_meses))
        renta_mensual_con_iva = renta_mensual_final * (1 + iva)
        pago_inicial = comision_apertura + rentas_anticipadas_mxn

        # Guardar datos del cliente
        cliente = Cliente(nombre=nombre_cliente, email=email_cliente, valor_arrendamiento=valor_arrendamiento,
                          renta_mensual=renta_mensual_con_iva, pago_inicial=pago_inicial)
        db.session.add(cliente)
        db.session.commit()

        # Resultados
        resultados = {
            'valor_con_iva': valor_con_iva,
            'valor_residual': valor_residual,
            'comision_apertura': comision_apertura,
            'rentas_anticipadas_mxn': rentas_anticipadas_mxn,
            'renta_mensual_con_iva': renta_mensual_con_iva,
            'pago_inicial': pago_inicial
        }
        return render_template('results.html', resultados=resultados, asesores=asesores)
    return render_template('index.html', asesores=asesores)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))