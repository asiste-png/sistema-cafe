from flask import Flask, render_template, request, redirect, session, url_for, send_file, send_from_directory
import sqlite3
import pandas as pd
import os
from datetime import datetime
import shutil

def crear_respaldo():
    carpeta_respaldo = r"C:\Users\samuel.alvarado\OneDrive - Tostaduria DelCafé S.A\RespaldoSistemaCafe"

    if not os.path.exists(carpeta_respaldo):
        os.makedirs(carpeta_respaldo)

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    origen = "cafe.db"
    destino = os.path.join(carpeta_respaldo, f"cafe_{fecha}.db")

    if os.path.exists(origen):
        shutil.copy2(origen, destino)
        print(f"✅ Respaldo creado: {destino}")

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

        return render_template("login.html", error="Usuario o contraseña incorrectos")

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
        fecha_ticket = request.form.get("fecha_ticket", "")
        finca_ticket = request.form.get("finca_ticket", "")
        fecha_registro = datetime.now().strftime("%d/%m/%Y %H:%M")
        usuario_actual = session.get("usuario", "Desconocido")

        nombre_imagen = ""
        if "imagen" in request.files:
            archivo = request.files["imagen"]
            if archivo.filename != "":
                nombre_imagen = archivo.filename
                ruta_imagen = os.path.join(app.config["UPLOAD_FOLDER"], nombre_imagen)
                archivo.save(ruta_imagen)

        conexion = sqlite3.connect("cafe.db")
        cursor = conexion.cursor()

        cursor.execute("""
        INSERT INTO registros (
            numero,
            productor,
            numero_comercial,
            finca,
            finca_ticket,
            tipo_cafe,
            pesado_inicial,
            pesado_final,
            quintales_bascula,
            imagen,
            fecha_registro,
            fecha_ticket,
            creado_por
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            numero,
            productor,
            numero_comercial,
            finca,
            finca_ticket,
            tipo_cafe,
            pesado_inicial,
            pesado_final,
            quintales_bascula,
            nombre_imagen,
            fecha_registro,
            fecha_ticket,
            usuario_actual
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inicio", guardado=1))

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM registros")
    total_registros = cursor.fetchone()[0]

    cursor.execute("SELECT IFNULL(SUM(quintales_bascula),0) FROM registros")
    total_quintales = round(cursor.fetchone()[0], 2)

    cursor.execute("SELECT COUNT(DISTINCT productor) FROM registros")
    total_productores = cursor.fetchone()[0]

    # Obtenemos lista de fincas únicas para sugerirlas en el formulario
    cursor.execute("SELECT DISTINCT finca FROM registros WHERE finca IS NOT NULL AND finca != '' ORDER BY finca")
    fincas_existentes = [fila[0] for fila in cursor.fetchall()]

    cursor.close()
    conexion.close()

    return render_template(
        "index.html",
        total_registros=total_registros,
        total_quintales=total_quintales,
        total_productores=total_productores,
        fincas_existentes=fincas_existentes
    )

# MOSTRAR IMÁGENES
@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario" not in session:
        return redirect("/login")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    if request.method == "POST":
        usuario_actual = session.get("usuario", "Desconocido")
        fecha_mod = datetime.now().strftime("%d/%m/%Y %H:%M")
        finca_ticket = request.form.get("finca_ticket", "")

        cursor.execute("""
        UPDATE registros
        SET
            numero=?,
            productor=?,
            numero_comercial=?,
            finca=?,
            finca_ticket=?,
            tipo_cafe=?,
            pesado_inicial=?,
            pesado_final=?,
            quintales_bascula=?,
            fecha_ticket=?,
            modificado_por=?,
            fecha_modificacion=?
        WHERE id=?
        """,
        (
            request.form["numero"],
            request.form["productor"],
            request.form["numero_comercial"],
            request.form["finca"],
            finca_ticket,
            request.form["tipo_cafe"],
            request.form["pesado_inicial"],
            request.form["pesado_final"],
            request.form["quintales_bascula"],
            request.form.get("fecha_ticket", ""),
            usuario_actual,
            fecha_mod,
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("registros"))

    cursor.execute("SELECT * FROM registros WHERE id=?", (id,))
    registro = cursor.fetchone()

    cursor.execute("SELECT DISTINCT finca FROM registros WHERE finca IS NOT NULL AND finca != '' ORDER BY finca")
    fincas_existentes = [fila[0] for fila in cursor.fetchall()]

    conexion.close()

    return render_template(
        "editar.html",
        registro=registro,
        fincas_existentes=fincas_existentes
    )

@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "usuario" not in session:
        return redirect("/login")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM registros WHERE id=?", (id,))
    conexion.commit()
    conexion.close()

    return redirect("/registros")

@app.route("/registros")
def registros():
    if "usuario" not in session:
        return redirect("/login")

    productor = request.args.get("productor", "")
    finca = request.args.get("finca", "")
    fecha = request.args.get("fecha", "")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    consulta = "SELECT * FROM registros WHERE 1=1"
    parametros = []

    if productor:
        consulta += " AND productor LIKE ?"
        parametros.append(f"%{productor}%")

    if finca:
        consulta += " AND finca LIKE ?"
        parametros.append(f"%{finca}%")

    if fecha:
        # Busca tanto en la fecha del ticket (YYYY-MM-DD) como en la fecha de registro
        consulta += " AND (fecha_ticket = ? OR fecha_registro LIKE ?)"
        parametros.extend([fecha, f"%{fecha}%"])

    consulta += " ORDER BY id DESC"

    cursor.execute(consulta, parametros)
    datos = cursor.fetchall()
    conexion.close()

    return render_template("registros.html", datos=datos)

@app.route("/exportar_excel")
def exportar_excel():
    if "usuario" not in session:
        return redirect("/login")

    conexion = sqlite3.connect("cafe.db")

    consulta = """
    SELECT
        numero AS 'No. Ticket',
        fecha_ticket AS 'Fecha Ticket',
        productor AS 'Productor',
        numero_comercial AS 'No. Comercial',
        finca AS 'Finca',
        tipo_cafe AS 'Tipo Café',
        pesado_inicial AS 'Pesado Inicial',
        pesado_final AS 'Pesado Final',
        quintales_bascula AS 'Quintales Báscula',
        fecha_registro AS 'Fecha Registro',
        creado_por AS 'Ingresado Por',
        modificado_por AS 'Modificado Por',
        fecha_modificacion AS 'Fecha Modificación'
    FROM registros
    ORDER BY id DESC
    """

    df = pd.read_sql_query(consulta, conexion)
    conexion.close()

    archivo_excel = "registros_cafe.xlsx"
    df.to_excel(archivo_excel, index=False)

    return send_file(archivo_excel, as_attachment=True)

@app.route("/usuarios")
def usuarios():
    if "usuario" not in session:
        return redirect("/login")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT id, usuario, rol, estado FROM usuarios ORDER BY usuario")
    datos = cursor.fetchall()
    conexion.close()

    return render_template("usuarios.html", datos=datos)

@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    if "usuario" not in session:
        return redirect("/login")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()

    if request.method == "POST":
        cursor.execute("""
        UPDATE usuarios
        SET usuario=?, password=?, rol=?, estado=?
        WHERE id=?
        """, (
            request.form["usuario"],
            request.form["password"],
            request.form["rol"],
            request.form["estado"],
            id
        ))
        conexion.commit()
        conexion.close()
        return redirect("/usuarios")

    cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))
    usuario = cursor.fetchone()
    conexion.close()

    return render_template("editar_usuario.html", usuario=usuario)

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if "usuario" not in session:
        return redirect("/login")

    conexion = sqlite3.connect("cafe.db")
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=?", (id,))
    conexion.commit()
    conexion.close()

    return redirect("/usuarios")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)