import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "estacionamiento.db"


def get_connection():
    """Devuelve una conexión a la base de datos con las foreign keys activadas."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # permite acceder a las columnas por nombre
    return conn


def hash_password(password: str) -> str:
    """Genera un hash SHA-256 de la contraseña (nunca se guarda en texto plano)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    """Crea las tablas si no existen y un usuario administrador por defecto."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL CHECK (rol IN ('admin', 'conductor'))
        )
    """)

    # Cada fila es una "empresa" de estacionamiento (un predio con sus propios lugares)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estacionamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lugares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL,
            tipo_vehiculo TEXT NOT NULL CHECK (tipo_vehiculo IN ('auto', 'moto', 'camioneta')),
            precio_hora REAL NOT NULL,
            disponible INTEGER NOT NULL DEFAULT 1,
            estacionamiento_id INTEGER NOT NULL,
            FOREIGN KEY (estacionamiento_id) REFERENCES estacionamientos(id) ON DELETE CASCADE,
            UNIQUE (numero, estacionamiento_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lugar_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            fecha_reserva TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'finalizada', 'cancelada')),
            FOREIGN KEY (lugar_id) REFERENCES lugares(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    # Usuario admin por defecto para poder entrar la primera vez
    cur.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "Administrador", "admin"),
        )

    # Un par de estacionamientos de ejemplo, para no arrancar con la lista vacía
    cur.execute("SELECT COUNT(*) AS total FROM estacionamientos")
    if cur.fetchone()["total"] == 0:
        cur.executemany(
            "INSERT INTO estacionamientos (nombre, direccion) VALUES (?, ?)",
            [
                ("Estacionamiento Cine Santa Fe", "Rivera 1111"),
                ("Estacionamientos Matuka", "San Jeronimo Norte 1211"),
                ("Terminal Norte", "Km 25"),
            ],
        )

    conn.commit()
    conn.close()



# USUARIOS
def crear_usuario(username, password, nombre, rol):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), nombre, rol),
        )
        conn.commit()
        return True, "Usuario creado correctamente"
    except sqlite3.IntegrityError:
        return False, "El nombre de usuario ya existe"
    finally:
        conn.close()


def validar_login(username, password):
    """Devuelve la fila del usuario si las credenciales son correctas, sino None."""
    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? AND password = ?",
        (username, hash_password(password)),
    )
    usuario = cur.fetchone()
    conn.close()
    return usuario


# ESTACIONAMIENTOS
def obtener_estacionamientos():
    conn = get_connection()
    cur = conn.execute("SELECT * FROM estacionamientos ORDER BY nombre")
    estacionamientos = cur.fetchall()
    conn.close()
    return estacionamientos


def obtener_estacionamiento_por_id(estacionamiento_id):
    conn = get_connection()
    cur = conn.execute("SELECT * FROM estacionamientos WHERE id = ?", (estacionamiento_id,))
    estacionamiento = cur.fetchone()
    conn.close()
    return estacionamiento


def contar_lugares(estacionamiento_id):
    """Devuelve (total_lugares, lugares_disponibles) de un estacionamiento, para mostrar en la card."""
    conn = get_connection()
    cur = conn.execute(
        """SELECT COUNT(*) AS total, SUM(disponible) AS disponibles
           FROM lugares WHERE estacionamiento_id = ?""",
        (estacionamiento_id,),
    )
    fila = cur.fetchone()
    conn.close()
    total = fila["total"] or 0
    disponibles = fila["disponibles"] or 0
    return total, disponibles


def agregar_estacionamiento(nombre, direccion):
    conn = get_connection()
    conn.execute(
        "INSERT INTO estacionamientos (nombre, direccion) VALUES (?, ?)",
        (nombre, direccion),
    )
    conn.commit()
    conn.close()
    return True, "Estacionamiento agregado correctamente"



# LUGARES
def agregar_lugar(numero, tipo_vehiculo, precio_hora, estacionamiento_id):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO lugares (numero, tipo_vehiculo, precio_hora, disponible, estacionamiento_id)
               VALUES (?, ?, ?, 1, ?)""",
            (numero, tipo_vehiculo, precio_hora, estacionamiento_id),
        )
        conn.commit()
        return True, "Lugar agregado correctamente"
    except sqlite3.IntegrityError:
        return False, "Ya existe un lugar con ese número en este estacionamiento"
    finally:
        conn.close()


def modificar_lugar(lugar_id, numero, tipo_vehiculo, precio_hora, disponible):
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE lugares
               SET numero = ?, tipo_vehiculo = ?, precio_hora = ?, disponible = ?
               WHERE id = ?""",
            (numero, tipo_vehiculo, precio_hora, int(disponible), lugar_id),
        )
        conn.commit()
        return True, "Lugar actualizado correctamente"
    except sqlite3.IntegrityError:
        return False, "Ya existe un lugar con ese número"
    finally:
        conn.close()


def borrar_lugar(lugar_id):
    conn = get_connection()
    conn.execute("DELETE FROM lugares WHERE id = ?", (lugar_id,))
    conn.commit()
    conn.close()


def obtener_lugares(estacionamiento_id, solo_disponibles=False):
    """Lugares de UN estacionamiento puntual (siempre filtramos por estacionamiento_id)."""
    conn = get_connection()
    if solo_disponibles:
        cur = conn.execute(
            "SELECT * FROM lugares WHERE estacionamiento_id = ? AND disponible = 1 ORDER BY numero",
            (estacionamiento_id,),
        )
    else:
        cur = conn.execute(
            "SELECT * FROM lugares WHERE estacionamiento_id = ? ORDER BY numero",
            (estacionamiento_id,),
        )
    lugares = cur.fetchall()
    conn.close()
    return lugares


def obtener_lugar_por_id(lugar_id):
    conn = get_connection()
    cur = conn.execute("SELECT * FROM lugares WHERE id = ?", (lugar_id,))
    lugar = cur.fetchone()
    conn.close()
    return lugar



# RESERVAS
def reservar_lugar(lugar_id, usuario_id):
    """Marca el lugar como no disponible y crea el registro de reserva."""
    conn = get_connection()
    lugar = conn.execute("SELECT * FROM lugares WHERE id = ?", (lugar_id,)).fetchone()
    if lugar is None or lugar["disponible"] == 0:
        conn.close()
        return False, "El lugar ya no está disponible"

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO reservas (lugar_id, usuario_id, fecha_reserva, estado) VALUES (?, ?, ?, 'activa')",
        (lugar_id, usuario_id, fecha),
    )
    conn.execute("UPDATE lugares SET disponible = 0 WHERE id = ?", (lugar_id,))
    conn.commit()
    conn.close()
    return True, "Reserva realizada correctamente"


def cancelar_reserva(reserva_id):
    """Cancela la reserva y vuelve a liberar el lugar."""
    conn = get_connection()
    reserva = conn.execute("SELECT * FROM reservas WHERE id = ?", (reserva_id,)).fetchone()
    if reserva is None:
        conn.close()
        return False, "Reserva no encontrada"

    conn.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (reserva_id,))
    conn.execute("UPDATE lugares SET disponible = 1 WHERE id = ?", (reserva["lugar_id"],))
    conn.commit()
    conn.close()
    return True, "Reserva cancelada, el lugar quedó disponible"


def obtener_reservas_usuario(usuario_id):
    conn = get_connection()
    cur = conn.execute(
        """SELECT reservas.id, reservas.fecha_reserva, reservas.estado,
                  lugares.numero, lugares.tipo_vehiculo, lugares.precio_hora,
                  estacionamientos.nombre AS estacionamiento_nombre
           FROM reservas
           JOIN lugares ON lugares.id = reservas.lugar_id
           JOIN estacionamientos ON estacionamientos.id = lugares.estacionamiento_id
           WHERE reservas.usuario_id = ?
           ORDER BY reservas.id DESC""",
        (usuario_id,),
    )
    reservas = cur.fetchall()
    conn.close()
    return reservas