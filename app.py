from flask import Flask, render_template, request, redirect, session, url_for, send_file, send_from_directory
import sqlite3
import pandas as pd
import os
from datetime import datetime
import shutil
from datetime import datetime

def crear_respaldo():

    carpeta_respaldo = r"C:\Users\samuel.alvarado\OneDrive - Tostaduria DelCafé S.A\RespaldoSistemaCafe"

    if not os.path.exists(carpeta_respaldo):
        os.makedirs(carpeta_respaldo)

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

    origen = "cafe.db"

    destino = os.path.join(
        carpeta_respaldo,
        f"cafe_{fecha}.db"
    )

    shutil.copy2(origen, destino)

    print(f"✅ Respaldo creado: {destino}")

    app = Flask(__name__)
    app.secret_key = "SamuelCafe2026"
crear_respaldo()



app = Flask(__name__)
app.secret_key = "SamuelCafe2026"

# Carpeta de imágenes
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form.get("usuario")
        password = request.form.get("password")

        print("Usuario:", usuario)
        print("Password:", password)

        conn = sqlite3.connect("cafe.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM usuarios
            WHERE usuario = ?
            AND password = ?
            AND estado = 'Activo'
        """, (usuario, password))

        usuario_encontrado = cursor.fetchone()

        conn.close()

        if usuario_encontrado:
            session["usuario"] = usuario
            return redirect(url_for("inicio"))

        return render_template(
            "login.html",
            error="Usuario o contraseña incorrectos"
        )

    return render_template("login.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# FORMULARIO PRINCIPAL
@app.route("/", methods=["GET", "POST"])
def inicio():

    if "usuario" not in session:
        return redirect("/login")

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

        return redirect(url_for("inicio", guardado=1))
    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM registros")
    total_registros = cursor.fetchone()[0]

    cursor.execute("""
        SELECT IFNULL(SUM(quintales_bascula),0)
        FROM registros
    """)
    total_quintales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT productor)
        FROM registros
    """)
    total_productores = cursor.fetchone()[0]

    cursor.close()
    conexion.close()

    return render_template(
        "index.html",
        total_registros=total_registros,
        total_quintales=total_quintales,
        total_productores=total_productores
    )

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

        return redirect(url_for("inicio", guardado=1))

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

    productor = request.args.get("productor", "")
    finca = request.args.get("finca", "")
    fecha = request.args.get("fecha", "")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    consulta = """
        SELECT *
        FROM registros
        WHERE 1=1
    """

    parametros = []

    if productor:
        consulta += " AND productor LIKE ?"
        parametros.append(f"%{productor}%")

    if finca:
        consulta += " AND finca LIKE ?"
        parametros.append(f"%{finca}%")

    if fecha:
        consulta += " AND fecha LIKE ?"
        parametros.append(f"%{fecha}%")

    consulta += " ORDER BY id DESC"

    cursor.execute(consulta, parametros)

    datos = cursor.fetchall()

    conexion.close()

    return render_template(
        "registros.html",
        datos=datos
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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
    