import sqlite3 as sql
import os

directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_db = os.path.join(directorio_actual, 'app_gestion.db')
conexion = sql.connect(ruta_db)


conexion = sql.connect('app_gestion.db')
cursor = conexion.cursor()

# activas las claves foraneas sqlite las trae desactivadas
cursor.execute("PRAGMA foreign_keys = ON;")


cursor.execute("""
CREATE TABLE IF NOT EXISTS TipoUsuario (
    id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
    rol_usuario TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS EstadoLugar (
    id_estado INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS TipoVehiculo (
    id_tipo_vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_vehiculo TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    mail TEXT,
    contraseña TEXT,
    id_rol INTEGER,
    FOREIGN KEY (id_rol) REFERENCES TipoUsuario (id_rol)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS lugares (
    id_lugar INTEGER PRIMARY KEY AUTOINCREMENT,
    num_lugar INTEGER,
    piso_o_sector TEXT, 
    precio REAL,
    id_tipo_vehiculo INTEGER,
    id_estado INTEGER,
    FOREIGN KEY (id_tipo_vehiculo) REFERENCES TipoVehiculo (id_tipo_vehiculo),
    FOREIGN KEY (id_estado) REFERENCES EstadoLugar (id_estado)
)
""")



cursor.execute("""
CREATE TABLE IF NOT EXISTS Administradores (
    id_administrador INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    id_usuario INTEGER,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios (id_usuario)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Conductores (
    id_conductor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    dni INTEGER,
    id_usuario INTEGER,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios (id_usuario)
)
""")



cursor.execute("""
CREATE TABLE IF NOT EXISTS Vehiculo (
    id_vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
    patente TEXT,
    id_conductor INTEGER,
    id_tipo_vehiculo INTEGER,
    FOREIGN KEY (id_conductor) REFERENCES Conductores (id_conductor),
    FOREIGN KEY (id_tipo_vehiculo) REFERENCES TipoVehiculo (id_tipo_vehiculo)
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS Reservas (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    estado_reserva INTEGER, 
    fecha_reserva TEXT, 
    hora_inicio TEXT, 
    hora_fin TEXT,
    id_conductor INTEGER,
    id_lugar INTEGER,
    id_vehiculo INTEGER,
    FOREIGN KEY (id_conductor) REFERENCES Conductores (id_conductor),
    FOREIGN KEY (id_lugar) REFERENCES lugares (id_lugar),
    FOREIGN KEY (id_vehiculo) REFERENCES Vehiculo (id_vehiculo)
)
""") 

cursor.execute("""
CREATE TABLE IF NOT EXISTS Pagos (
    id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    monto REAL,
    metodo_pago TEXT,
    fecha_pago TEXT, 
    id_reserva INTEGER,
    FOREIGN KEY (id_reserva) REFERENCES Reservas (id_reserva)
)
""")

# Guardar los cambios y cerrar
conexion.commit()
print("Base de datos creada exitosamente con sus relaciones.")
conexion.close()