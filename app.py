from flask import Flask, render_template, request
from models import db, Cliente, Asesor
import os
import locale
import requests
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clientes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Set locale for number formatting (Spanish Mexico)
locale.setlocale(locale.LC_ALL, "es_MX.UTF-8")

# Custom filter for formatting numbers
@app.template_filter("format_currency")
def format_currency(value):
    return locale.format_string("%.2f", value, grouping=True)

# Initialize database tables and seed asesores
with app.app_context():
    db.create_all()
    if Asesor.query.count() == 0:
        asesores = [
            Asesor(nombre="Juan Pérez", email="juan@101finance.com", telefono="555-123-4567"),
            Asesor(nombre="María López", email="maria@101finance.com", telefono="555-987-6543")
        ]
        db.session.bulk_save_objects(asesores)
        db.session.commit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Extract form data
        valor_arrendamiento = float(request.form["valor_arrendamiento"])
        tasa_anual = float(request.form["tasa_anual"])
        plazo_meses = int(request.form["plazo_meses"])
        valor_residual = float(request.form["valor_residual"])
        comision_apertura = float(request.form["comision_apertura"])
        rentas_anticipadas = int(request.form["rentas_anticipadas"])
        nombre_cliente = request.form["nombre_cliente"]
        email_cliente = request.form["email_cliente"]

        # Calculations (base in MXN)
        valor_con_iva = valor_arrendamiento * 1.16
        renta_mensual_con_iva = (valor_arrendamiento * tasa_anual / 1200) / (1 - (1 + tasa_anual / 1200) ** -plazo_meses)
        pago_inicial = renta_mensual_con_iva * rentas_anticipadas + (valor_arrendamiento * comision_apertura / 100)

        # Save to database
        cliente = Cliente(
            nombre=nombre_cliente,
            email=email_cliente,
            valor_arrendamiento=valor_arrendamiento,
            renta_mensual=renta_mensual_con_iva,
            pago_inicial=pago_inicial
        )
        db.session.add(cliente)
        db.session.commit()

        # Fetch USD/MXN exchange rate
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        data = response.json()
        exchange_rate = data["rates"]["MXN"] if data["result"] == "success" else 20.0  # Fallback rate
        current_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        resultados = {
            "valor_con_iva": valor_con_iva,
            "valor_residual": valor_arrendamiento * valor_residual / 100,
            "comision_apertura": valor_arrendamiento * comision_apertura / 100,
            "rentas_anticipadas_mxn": renta_mensual_con_iva * rentas_anticipadas,
            "renta_mensual_con_iva": renta_mensual_con_iva,
            "pago_inicial": pago_inicial
        }
        asesores = Asesor.query.all()
        return render_template("results.html", resultados=resultados, asesores=asesores, exchange_rate=exchange_rate, current_date=current_date)

    asesores = Asesor.query.all()
    return render_template("index.html", asesores=asesores)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
