from database.conexion import obtener_conexion

# ==========================================
# 1. AUTENTICACIÓN Y USUARIOS
# ==========================================

def verificar_credenciales(email, clave):
    """Verifica el correo y contraseña. Retorna los datos del usuario si coincide."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("""
        SELECT u.id_usuario, u.mail, u.id_rol, r.rol_usuario 
        FROM Usuarios u
        JOIN TipoUsuario r ON u.id_rol = r.id_rol
        WHERE u.mail = ? AND u.contraseña = ?
    """, (email, clave))
    
    usuario = cursor.fetchone()
    conexion.close()
    return usuario


def registrar_usuario(mail, contraseña, nombre, dni, rol="Conductor"):
    """Registra un nuevo usuario asegurando la existencia previa del rol en la base de datos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    try:
        # 1. Autoreparación: Garantiza que los roles existan en TipoUsuario
        cursor.execute("INSERT OR IGNORE INTO TipoUsuario (id_rol, rol_usuario) VALUES (1, 'Administrador')")
        cursor.execute("INSERT OR IGNORE INTO TipoUsuario (id_rol, rol_usuario) VALUES (2, 'Conductor')")

        # 2. Buscar id_rol
        cursor.execute("SELECT id_rol FROM TipoUsuario WHERE rol_usuario = ?", (rol,))
        res_rol = cursor.fetchone()
        id_rol = res_rol[0] if res_rol else 2

        # 3. Insertar Usuario
        cursor.execute(
            "INSERT INTO Usuarios (mail, contraseña, id_rol) VALUES (?, ?, ?)",
            (mail, contraseña, id_rol)
        )
        id_usuario = cursor.lastrowid

        # 4. Insertar Conductor
        cursor.execute(
            "INSERT INTO Conductores (nombre, dni, id_usuario) VALUES (?, ?, ?)",
            (nombre, int(dni), id_usuario)
        )

        conexion.commit()
        return True, "¡Usuario registrado exitosamente!"
    except Exception as e:
        conexion.rollback()
        err = str(e)
        if "UNIQUE constraint failed: Usuarios.mail" in err:
            return False, "El correo electrónico ya está registrado."
        elif "UNIQUE constraint failed: Conductores.dni" in err:
            return False, "El DNI ingresado ya pertenece a otro usuario."
        else:
            return False, f"Error de registro: {err}"
    finally:
        conexion.close()


def obtener_id_conductor(id_usuario):
    """Retorna el id_conductor asociado a un id_usuario."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_conductor FROM Conductores WHERE id_usuario = ?", (id_usuario,))
    res = cursor.fetchone()
    conexion.close()
    return res[0] if res else None


# ==========================================
# 2. GESTIÓN DE VEHÍCULOS
# ==========================================

def registrar_vehiculo(patente, id_conductor, id_tipo_vehiculo):
    """Registra una nueva patente asociada a un conductor."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "INSERT INTO Vehiculo (patente, id_conductor, id_tipo_vehiculo) VALUES (?, ?, ?)",
            (patente.upper().strip(), id_conductor, id_tipo_vehiculo)
        )
        conexion.commit()
        return True, "Vehículo registrado con éxito."
    except Exception as e:
        conexion.rollback()
        if "UNIQUE constraint failed: Vehiculo.patente" in str(e):
            return False, "La patente ya se encuentra registrada."
        return False, f"Error al registrar vehículo: {str(e)}"
    finally:
        conexion.close()


def obtener_vehiculos_conductor(id_conductor):
    """Retorna la lista de vehículos de un conductor."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT v.id_vehiculo, v.patente, tv.tipo_vehiculo 
        FROM Vehiculo v
        JOIN TipoVehiculo tv ON v.id_tipo_vehiculo = tv.id_tipo_vehiculo
        WHERE v.id_conductor = ?
    """, (id_conductor,))
    vehiculos = cursor.fetchall()
    conexion.close()
    return vehiculos


# ==========================================
# 3. ZONAS Y LUGARES DE ESTACIONAMIENTO
# ==========================================

def obtener_lugares_por_zona(piso_o_sector):
    """Retorna los lugares según el sector (ej. 'Centro', 'Norte') con su estado."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT l.id_lugar, l.num_lugar, l.piso_o_sector, l.precio, e.descripcion AS estado, tv.tipo_vehiculo
        FROM lugares l
        JOIN EstadoLugar e ON l.id_estado = e.id_estado
        JOIN TipoVehiculo tv ON l.id_tipo_vehiculo = tv.id_tipo_vehiculo
        WHERE l.piso_o_sector = ?
    """, (piso_o_sector,))
    lugares = cursor.fetchall()
    conexion.close()
    return lugares


def agregar_lugar_estacionamiento(num_lugar, piso_o_sector, precio, id_tipo_vehiculo, id_estado=1):
    """Agrega una plaza de estacionamiento nueva (Útil para perfil Administrador)."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO lugares (num_lugar, piso_o_sector, precio, id_tipo_vehiculo, id_estado)
        VALUES (?, ?, ?, ?, ?)
    """, (num_lugar, piso_o_sector, precio, id_tipo_vehiculo, id_estado))
    conexion.commit()
    conexion.close()


# ==========================================
# 4. RESERVAS Y PAGOS
# ==========================================

def crear_reserva(fecha, hora_inicio, hora_fin, id_conductor, id_lugar, id_vehiculo):
    """Crea una reserva de lugar y cambia el estado del lugar a 'Reservado' (id_estado = 3)."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # 1. Crear la reserva
        cursor.execute("""
            INSERT INTO Reservas (estado_reserva, fecha_reserva, hora_inicio, hora_fin, id_conductor, id_lugar, id_vehiculo)
            VALUES (1, ?, ?, ?, ?, ?, ?)
        """, (fecha, hora_inicio, hora_fin, id_conductor, id_lugar, id_vehiculo))
        id_reserva = cursor.lastrowid

        # 2. Actualizar el estado del lugar a 'Reservado' (id_estado = 3)
        cursor.execute("UPDATE lugares SET id_estado = 3 WHERE id_lugar = ?", (id_lugar,))

        conexion.commit()
        return True, id_reserva
    except Exception as e:
        conexion.rollback()
        return False, str(e)
    finally:
        conexion.close()


def registrar_pago(monto, metodo_pago, fecha_pago, id_reserva):
    """Registra el comprobante de pago de una reserva."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO Pagos (monto, metodo_pago, fecha_pago, id_reserva)
            VALUES (?, ?, ?, ?)
        """, (monto, metodo_pago, fecha_pago, id_reserva))
        conexion.commit()
        return True, "Pago registrado correctamente."
    except Exception as e:
        conexion.rollback()
        return False, f"Error en el pago: {str(e)}"
    finally:
        conexion.close()