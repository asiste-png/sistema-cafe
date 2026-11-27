from flask import Flask, render_template, request, redirect, session, url_for, send_file
import psycopg2
import pandas as pd
import os
import io
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "SamuelCafe2026")

# Credenciales de Supabase (se configuran en Render -> Environment Variables)
DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
SUPABASE_KEY = (os.environ.get("SUPABASE_KEY") or "").strip()
BUCKET_NAME = "tickets"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Crea las tablas en Supabase PostgreSQL si aún no existen y un usuario admin inicial."""
    if not DATABASE_URL:
        print("⚠️ Falta configurar DATABASE_URL")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'Usuario',
            estado TEXT DEFAULT 'Activo'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id SERIAL PRIMARY KEY,
            numero TEXT,
            productor TEXT,
            numero_comercial TEXT,
            finca TEXT,
            tipo_cafe TEXT,
            pesado_inicial DOUBLE PRECISION,
            pesado_final DOUBLE PRECISION,
            quintales_bascula DOUBLE PRECISION,
            imagen TEXT,
            fecha_registro TEXT,
            fecha_ticket TEXT,
            creado_por TEXT,
            modificado_por TEXT,
            fecha_modificacion TEXT,
            finca_ticket TEXT,
            tipo_movimiento TEXT,
            estado_pago TEXT DEFAULT 'No pagado'
        )
    """)

    # Crea usuario admin por defecto si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (usuario, password, rol, estado)
            VALUES (%s, %s, %s, %s)
        """, ("admin", "admin123", "Administrador", "Activo"))

    conn.commit()
    cursor.close()
    conn.close()


init_db()


def a_float(valor):
    try:
        return float(valor) if valor not in (None, "") else 0.0
    except ValueError:
        return 0.0


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, usuario, rol
            FROM usuarios
            WHERE usuario = %s
            AND password = %s
            AND estado = 'Activo'
        """, (usuario, password))

        usuario_encontrado = cursor.fetchone()
        cursor.close()
        conn.close()

        if usuario_encontrado:
            session["usuario"] = usuario_encontrado[1]
            session["rol"] = usuario_encontrado[2].strip().lower()
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
        try:
            numero = request.form.get("numero", "")
            productor = request.form.get("productor", "")
            numero_comercial = request.form.get("numero_comercial", "")
            finca = request.form.get("finca", "")
            tipo_cafe = request.form.get("tipo_cafe", "")
            tipo_movimiento = request.form.get("tipo_movimiento", "")
            pesado_inicial = a_float(request.form.get("pesado_inicial"))
            pesado_final = a_float(request.form.get("pesado_final"))
            quintales_bascula = a_float(request.form.get("quintales_bascula"))
            fecha_ticket = request.form.get("fecha_ticket", "")
            finca_ticket = request.form.get("finca_ticket", "")
            fecha_registro = datetime.now().strftime("%d/%m/%Y %H:%M")
            usuario_actual = session.get("usuario", "Desconocido")

            nombre_imagen = ""
            if "imagen" in request.files:
                archivo = request.files["imagen"]
                if archivo and archivo.filename != "" and supabase:
                    try:
                        nombre_limpio = secure_filename(archivo.filename)
                        nombre_imagen = f"{uuid.uuid4().hex[:8]}_{nombre_limpio}"
                        contenido = archivo.read()
                        content_type = archivo.content_type or "image/jpeg"

                        supabase.storage.from_(BUCKET_NAME).upload(
                            path=nombre_imagen,
                            file=contenido,
                            file_options={"content-type": content_type}
                        )
                    except Exception as img_err:
                        print(f"⚠️ No se pudo subir la imagen a Storage: {img_err}")
                        nombre_imagen = ""

            conexion = get_db_connection()
            cursor = conexion.cursor()

            cursor.execute("""
INSERT INTO registros (
    numero,
    productor,
    numero_comercial,
    finca,
    finca_ticket,
    tipo_cafe,
    tipo_movimiento,
    pesado_inicial,
    pesado_final,
    quintales_bascula,
    imagen,
    fecha_registro,
    fecha_ticket,
    creado_por
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    numero,
    productor,
    numero_comercial,
    finca,
    finca_ticket,
    tipo_cafe,
    tipo_movimiento,
    pesado_inicial,
    pesado_final,
    quintales_bascula,
    nombre_imagen,
    fecha_registro,
    fecha_ticket,
    usuario_actual
))

            conexion.commit()
            cursor.close()
            conexion.close()

            return redirect(url_for("inicio", guardado=1))

        except Exception as e:
            return f"<h3>Error exacto al guardar:</h3><pre>{e}</pre>"

    conexion = get_db_connection()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM registros")
    total_registros = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quintales_bascula), 0) FROM registros")
    total_quintales = round(float(cursor.fetchone()[0]), 2)

    cursor.execute("SELECT COUNT(DISTINCT productor) FROM registros")
    total_productores = cursor.fetchone()[0]

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


# MOSTRAR IMÁGENES DESDE SUPABASE STORAGE
@app.route("/uploads/<path:filename>")
def uploads(filename):
    if filename.startswith("http"):
        return redirect(filename)
    url_publica = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
    return redirect(url_publica)


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario" not in session:
        return redirect("/login")

    conexion = get_db_connection()
    cursor = conexion.cursor()

    if request.method == "POST":
        usuario_actual = session.get("usuario", "Desconocido")
        fecha_mod = datetime.now().strftime("%d/%m/%Y %H:%M")
        finca_ticket = request.form.get("finca_ticket", "")
        tipo_movimiento = request.form.get("tipo_movimiento", "")
        estado_pago = request.form.get("estado_pago", "No pagado")

        cursor.execute("""
        UPDATE registros
        SET
            numero=%s,
            productor=%s,
            numero_comercial=%s,
            finca=%s,
            finca_ticket=%s,
            tipo_cafe=%s,
            tipo_movimiento=%s,
            estado_pago=%s,
            pesado_inicial=%s,
            pesado_final=%s,
            quintales_bascula=%s,
            fecha_ticket=%s,
            modificado_por=%s,
            fecha_modificacion=%s
        WHERE id=%s
        """, (
            request.form["numero"],
            request.form["productor"],
            request.form["numero_comercial"],
            request.form["finca"],
            finca_ticket,
            request.form["tipo_cafe"],
            tipo_movimiento,
            estado_pago,
            a_float(request.form["pesado_inicial"]),
            a_float(request.form["pesado_final"]),
            a_float(request.form["quintales_bascula"]),
            request.form.get("fecha_ticket", ""),
            usuario_actual,
            fecha_mod,
            id
        ))

        conexion.commit()
        cursor.close()
        conexion.close()

        return redirect(url_for("registros"))

    cursor.execute("""
        SELECT id, numero, productor, numero_comercial, finca, tipo_cafe,
               pesado_inicial, pesado_final, quintales_bascula, imagen,
               fecha_registro, fecha_ticket, creado_por, modificado_por,
               fecha_modificacion, finca_ticket, tipo_movimiento, estado_pago
        FROM registros WHERE id=%s
    """, (id,))
    registro = cursor.fetchone()

    cursor.execute("SELECT DISTINCT finca FROM registros WHERE finca IS NOT NULL AND finca != '' ORDER BY finca")
    fincas_existentes = [fila[0] for fila in cursor.fetchall()]

    cursor.close()
    conexion.close()

    return render_template(
        "editar.html",
        registro=registro,
        fincas_existentes=fincas_existentes
    )


@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "usuario" not in session or session.get("rol") not in ("admin", "admi", "administrador"):
        return redirect("/registros")

    conexion = get_db_connection()
    cursor = conexion.cursor()

    # Borra también la imagen en Supabase Storage si existe
    cursor.execute("SELECT imagen FROM registros WHERE id=%s", (id,))
    fila = cursor.fetchone()
    if fila and fila[0] and supabase:
        try:
            supabase.storage.from_(BUCKET_NAME).remove([fila[0]])
        except Exception:
            pass

    cursor.execute("DELETE FROM registros WHERE id=%s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect("/registros")


@app.route("/registros")
def registros():
    if "usuario" not in session:
        return redirect("/login")

    ticket = request.args.get("ticket", "").strip()
    productor = request.args.get("productor", "").strip()
    finca = request.args.get("finca", "").strip()
    fecha = request.args.get("fecha", "").strip()

    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
    except ValueError:
        pagina = 1

    por_pagina = 20
    offset = (pagina - 1) * por_pagina

    conexion = get_db_connection()
    cursor = conexion.cursor()

    where_sql = " WHERE 1=1"
    parametros = []

    if ticket:
        where_sql += " AND numero ILIKE %s"
        parametros.append(f"%{ticket}%")

    if productor:
        where_sql += " AND productor ILIKE %s"
        parametros.append(f"%{productor}%")

    if finca:
        where_sql += " AND (finca ILIKE %s OR finca_ticket ILIKE %s)"
        parametros.extend([f"%{finca}%", f"%{finca}%"])

    if fecha:
        where_sql += " AND (fecha_ticket = %s OR fecha_registro ILIKE %s)"
        parametros.extend([fecha, f"%{fecha}%"])

    cursor.execute(
        f"SELECT COUNT(*), COALESCE(SUM(quintales_bascula), 0) FROM registros {where_sql}",
        parametros
    )
    resumen = cursor.fetchone()
    total_registros = resumen[0] or 0
    total_quintales = round(float(resumen[1] or 0), 2)
    total_paginas = max(1, (total_registros + por_pagina - 1) // por_pagina)

    if pagina > total_paginas:
        pagina = total_paginas
        offset = (pagina - 1) * por_pagina

    consulta = f"""
        SELECT id, numero, productor, numero_comercial, finca, tipo_cafe,
               pesado_inicial, pesado_final, quintales_bascula, imagen,
               fecha_registro, fecha_ticket, creado_por, modificado_por,
               fecha_modificacion, finca_ticket, tipo_movimiento, estado_pago
        FROM registros
        {where_sql}
        ORDER BY
            NULLIF(regexp_replace(COALESCE(numero, ''), '[^0-9]', '', 'g'), '')::bigint DESC NULLS LAST,
            numero DESC,
            id DESC
        LIMIT %s OFFSET %s
    """

    cursor.execute(consulta, parametros + [por_pagina, offset])
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template(
        "registros.html",
        datos=datos,
        total_quintales=total_quintales,
        total_registros=total_registros,
        pagina=pagina,
        total_paginas=total_paginas,
        offset=offset,
        ticket=ticket,
        productor=productor,
        finca=finca,
        fecha=fecha
    )


@app.route("/exportar_excel")
def exportar_excel():
    if "usuario" not in session:
        return redirect("/login")

    conexion = get_db_connection()

    consulta = """
    SELECT
        numero AS "No. Ticket",
        fecha_ticket AS "Fecha Ticket",
        productor AS "Productor",
        numero_comercial AS "No. Comercial",
        finca AS "Finca",
        finca_ticket AS "Finca Ticket",
        tipo_cafe AS "Tipo Café",
        tipo_movimiento AS "Movimiento",
        estado_pago AS "Estado Pago",
        pesado_inicial AS "Pesado Inicial",
        pesado_final AS "Pesado Final",
        quintales_bascula AS "Quintales Báscula",
        fecha_registro AS "Fecha Registro",
        creado_por AS "Ingresado Por",
        modificado_por AS "Modificado Por",
        fecha_modificacion AS "Fecha Modificación"
    FROM registros
    ORDER BY id DESC
    """

    df = pd.read_sql_query(consulta, conexion)
    conexion.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Registros")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="registros_cafe.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/usuarios")
def usuarios():
    if "usuario" not in session or session.get("rol") not in ("admin", "admi", "administrador"):
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor()

    cursor.execute("SELECT id, usuario, rol, estado FROM usuarios ORDER BY usuario")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template("usuarios.html", datos=datos)


@app.route("/nuevo_usuario", methods=["GET", "POST"])
def nuevo_usuario():
    if "usuario" not in session or session.get("rol") not in ("admin", "admi", "administrador"):
        return redirect("/")

    if request.method == "POST":
        conexion = get_db_connection()
        cursor = conexion.cursor()
        cursor.execute("""
        INSERT INTO usuarios (usuario, password, rol, estado)
        VALUES (%s, %s, %s, %s)
        """, (
            request.form["usuario"],
            request.form["password"],
            request.form["rol"],
            request.form.get("estado", "Activo")
        ))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect("/usuarios")

    return render_template("nuevo_usuario.html")


@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    if "usuario" not in session or session.get("rol") not in ("admin", "admi", "administrador"):
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor()

    if request.method == "POST":
        cursor.execute("""
        UPDATE usuarios
        SET usuario=%s, password=%s, rol=%s, estado=%s
        WHERE id=%s
        """, (
            request.form["usuario"],
            request.form["password"],
            request.form["rol"],
            request.form["estado"],
            id
        ))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect("/usuarios")

    cursor.execute("SELECT id, usuario, password, rol, estado FROM usuarios WHERE id=%s", (id,))
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()

    return render_template("editar_usuario.html", usuario=usuario)


@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if "usuario" not in session or session.get("rol") not in ("admin", "admi", "administrador"):
        return redirect("/")

    conexion = get_db_connection()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect("/usuarios")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)