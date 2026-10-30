import sqlite3

conexion = sqlite3.connect("cafe.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    numero TEXT,

    productor TEXT,

    numero_comercial TEXT,

    finca TEXT,

    tipo_cafe TEXT,

    pesado_inicial REAL,

    pesado_final REAL,

    quintales_bascula REAL,

    imagen TEXT,

    fecha_registro TEXT

)
""")

conexion.commit()
conexion.close()

print("✅ Base creada correctamente")