import sqlite3

conn = sqlite3.connect("cafe.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO usuarios (usuario, password, rol, estado)
VALUES (?, ?, ?, ?)
""", (
    "Alex",
    "Alex123",
    "Operador",
    "Activo"
))

conn.commit()
conn.close()

print("Usuario agregado correctamente")