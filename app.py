from flask import Flask, render_template, request, send_from_directory, redirect, send_file
import sqlite3
import pandas as pd
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


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        cursor.execute("""
        UPDATE registros
        SET
            numero=?,
            productor=?,
            numero_comercial=?,
            finca=?,
            tipo_cafe=?,
            pesado_inicial=?,
            pesado_final=?,
            quintales_bascula=?
        WHERE id=?
        """,
        (
            request.form["numero"],
            request.form["productor"],
            request.form["numero_comercial"],
            request.form["finca"],
            request.form["tipo_cafe"],
            request.form["pesado_inicial"],
            request.form["pesado_final"],
            request.form["quintales_bascula"],
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect("/registros")

    cursor.execute(
        "SELECT * FROM registros WHERE id=?",
        (id,)
    )

    registro = cursor.fetchone()

    conexion.close()

    return render_template(
        "editar.html",
        registro=registro
    )


@app.route("/eliminar/<int:id>")
def eliminar(id):

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM registros WHERE id=?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect("/registros")

@app.route("/registros")
def registros():

    busqueda = request.args.get("buscar", "")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    if busqueda:

        cursor.execute("""
            SELECT *
            FROM registros
            WHERE productor LIKE ?
            ORDER BY id DESC
        """, ('%' + busqueda + '%',))

    else:

        cursor.execute("""
            SELECT *
            FROM registros
            ORDER BY id DESC
        """)

    datos = cursor.fetchall()

    conexion.close()

    return render_template(
        "registros.html",
        datos=datos,
        busqueda=busqueda
    )

@app.route("/exportar_excel")
def exportar_excel():

    conexion = sqlite3.connect("cafe.db")

    consulta = """
    SELECT
        numero AS 'No.',
        productor AS 'Productor',
        numero_comercial AS 'No. Comercial',
        finca AS 'Finca',
        tipo_cafe AS 'Tipo Café',
        pesado_inicial AS 'Pesado Inicial',
        pesado_final AS 'Pesado Final',
        quintales_bascula AS 'Quintales Báscula',
        fecha_registro AS 'Fecha Registro'
    FROM registros
    """

    df = pd.read_sql_query(
        consulta,
        conexion
    )

    conexion.close()

    archivo_excel = "registros_cafe.xlsx"

    df.to_excel(
        archivo_excel,
        index=False
    )

    return send_file(
        archivo_excel,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )