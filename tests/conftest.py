import os

# La aplicación se importa durante la colección de pruebas: la configuración
# debe existir antes de que app.database cree su motor.
os.environ.setdefault("DATABASE_URL", "sqlite://")
