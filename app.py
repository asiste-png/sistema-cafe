from flask import Flask, render_template, request, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Carpeta de imágenes
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# FORMULARIO PRINCIPAL
@app.route("/", methods=["GET", "POST"])
def inicio():

    if request.method == "POST":

        numero = request.form["numero"]
        productor = request.form["productor"]
        numero_comercial = request.form["numero_comercial"]
        finca = request.form["finca"]
        tipo_cafe = request.form["tipo_cafe"]
        pesado_inicial = request.form["pesado_inicial"]
        pesado_final = request.form["pesado_final"]
        quintales_bascula = request.form["quintales_bascula"]

        fecha_registro = datetime.now().strftime("%d/%m/%Y %H:%M")

        nombre_imagen = ""

        if "imagen" in request.files:

            archivo = request.files["imagen"]

            if archivo.filename != "":
                nombre_imagen = archivo.filename

                ruta_imagen = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nombre_imagen
                )

                archivo.save(ruta_imagen)

        conexion = sqlite3.connect("cafe.db")
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO registros (
            numero,
            productor,
            numero_comercial,
            finca,
            tipo_cafe,
            pesado_inicial,
            pesado_final,
            quintales_bascula,
            imagen,
            fecha_registro
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            numero,
            productor,
            numero_comercial,
            finca,
            tipo_cafe,
            pesado_inicial,
            pesado_final,
            quintales_bascula,
            nombre_imagen,
            fecha_registro
        ))

        conexion.commit()
        conexion.close()

        return """
        <h2>✅ Registro guardado correctamente</h2>

        <a href="/">Nuevo Registro</a>

        <br><br>

        <a href="/registros">Ver Registros</a>
        """

    return render_template("index.html")


# MOSTRAR IMÁGENES
@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# LISTAR REGISTROS
@app.route("/registros")
def registros():

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT *
        FROM registros
        ORDER BY id DESC
    """)

    datos = cursor.fetchall()

    conexion.close()

    return render_template(
        "registros.html",
        datos=datos
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )