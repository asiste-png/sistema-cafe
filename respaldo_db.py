import shutil
from datetime import datetime

fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

origen = "cafe.db"

destino = rf"C:\Users\samuel.alvarado\OneDrive - Tostaduria DelCafé S.A\RespaldoSistemaCafe\cafe_{fecha}.db"

shutil.copy2(origen, destino)

print("Respaldo realizado correctamente")