from database.conexion import obtener_conexion


def registrar_usuario(mail, contraseña, nombre, dni, rol="Conductor"):
    """
    Registra un nuevo usuario en la base de datos.
    Crea el registro en la tabla Usuarios y luego en Conductores.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    try:
        # Obtener id_rol según el tipo seleccionando de TipoUsuario
        cursor.execute("SELECT id_rol FROM TipoUsuario WHERE rol_usuario = ?", (rol,))
        resultado_rol = cursor.fetchone()
        id_rol = resultado_rol[0] if resultado_rol else 2 

        #Insertar en la tabla Usuarios
        cursor.execute(
            "INSERT INTO Usuarios (mail, contraseña, id_rol) VALUES (?, ?, ?)",
            (mail, contraseña, id_rol)
        )
        id_usuario = cursor.lastrowid

        #Insertar en la tabla Conductores
        cursor.execute(
            "INSERT INTO Conductores (nombre, dni, id_usuario) VALUES (?, ?, ?)",
            (nombre, int(dni), id_usuario)
        )

        conexion.commit()
        return True, "¡Usuario registrado exitosamente!"
    except Exception as e:
        conexion.rollback()
        if "UNIQUE constraint failed: Usuarios.mail" in str(e):
            return False, "El correo electrónico ya está registrado."
        elif "UNIQUE constraint failed: Conductores.dni" in str(e):
            return False, "El DNI ya se encuentra registrado."
        else:
            return False, f"Error al registrar: {str(e)}"
    finally:
        conexion.close()

def verificar_credenciales(email, clave):
    """Verifica si el correo y la contraseña coinciden en la base de datos."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute(
        "SELECT id_usuario, mail, id_rol FROM Usuarios WHERE mail = ? AND contraseña = ?", 
        (email, clave)
    )
    usuario = cursor.fetchone()
    conexion.close()
    
    return usuario


import flet as ft
from database.conexion import crear_tablas
from database.consultas import verificar_credenciales, registrar_usuario


def main(pagina: ft.Page):
    # Asegura que la base de datos y sus tablas estén creadas al iniciar
    crear_tablas()

    pagina.bgcolor = ft.Colors.INDIGO_ACCENT_100
    pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    pagina.vertical_alignment = ft.MainAxisAlignment.CENTER
    pagina.title = "Estacionamiento App"

    # Variable para guardar la información del usuario en sesión
    usuario_actual = None

    #INICIO DE SESIÓN
    def mostrar_login():
        pagina.clean()
        pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

        campo_usuario = ft.TextField(label="Correo electrónico", width=300)
        campo_clave = ft.TextField(
            label="Contraseña", 
            password=True, 
            can_reveal_password=True, 
            width=300
        )
        mensaje = ft.Text("", color=ft.Colors.RED_400)

        def ingresar(e):
            nonlocal usuario_actual
            if not campo_usuario.value or not campo_clave.value:
                mensaje.value = "Por favor, complete todos los campos."
                mensaje.color = ft.Colors.RED_400
                pagina.update()
                return

            usuario = verificar_credenciales(campo_usuario.value, campo_clave.value)
            if usuario:
                usuario_actual = usuario
                mostrar_menu_principal()
            else:
                mensaje.value = "Correo o contraseña incorrectos."
                mensaje.color = ft.Colors.RED_400
                pagina.update()

        boton_ingresar = ft.FilledButton("Iniciar Sesión", on_click=ingresar, width=300)
        boton_ir_registro = ft.TextButton("¿No tienes cuenta? Regístrate aquí", on_click=lambda e: mostrar_registro())

        pagina.add(
            ft.Text("Iniciar Sesión", size=26, weight=ft.FontWeight.BOLD),
            campo_usuario,
            campo_clave,
            mensaje,
            boton_ingresar,
            boton_ir_registro
        )

    #REGISTRO DE USUARIO
    def mostrar_registro():
        pagina.clean()
        pagina.vertical_alignment = ft.MainAxisAlignment.CENTER

        campo_nombre = ft.TextField(label="Nombre Completo", width=300)
        campo_dni = ft.TextField(label="DNI", width=300, keyboard_type=ft.KeyboardType.NUMBER)
        campo_email = ft.TextField(label="Correo electrónico", width=300)
        campo_clave = ft.TextField(
            label="Contraseña", 
            password=True, 
            can_reveal_password=True, 
            width=300
        )
        mensaje_estado = ft.Text("", size=14)

        def procesar_registro(e):
            # Validaciones de entrada
            if not campo_nombre.value or not campo_dni.value or not campo_email.value or not campo_clave.value:
                mensaje_estado.value = "Todos los campos son obligatorios."
                mensaje_estado.color = ft.Colors.RED_400
                pagina.update()
                return

            if not campo_dni.value.isdigit():
                mensaje_estado.value = "El DNI debe contener solo números."
                mensaje_estado.color = ft.Colors.RED_400
                pagina.update()
                return

            # Intenta guardar el usuario en la base de datos
            exito, msg = registrar_usuario(
                mail=campo_email.value.strip(),
                contraseña=campo_clave.value.strip(),
                nombre=campo_nombre.value.strip(),
                dni=campo_dni.value.strip()
            )

            if exito:
                mensaje_estado.value = msg
                mensaje_estado.color = ft.Colors.GREEN_400
                pagina.update()
                # Redirige al login tras registrar
                mostrar_login()
            else:
                mensaje_estado.value = msg
                mensaje_estado.color = ft.Colors.RED_400
                pagina.update()

        boton_guardar = ft.FilledButton("Registrarse", on_click=procesar_registro, width=300)
        boton_volver = ft.OutlinedButton("Volver al Login", on_click=lambda e: mostrar_login(), width=300)

        pagina.add(
            ft.Text("Registro de Conductor", size=26, weight=ft.FontWeight.BOLD),
            campo_nombre,
            campo_dni,
            campo_email,
            campo_clave,
            mensaje_estado,
            boton_guardar,
            boton_volver
        )

    #MENÚ PRINCIPAL
    def mostrar_menu_principal():
        pagina.clean()
        pagina.vertical_alignment = ft.MainAxisAlignment.START

        texto_bienvenida = ft.Text(f"Bienvenido {usuario_actual[1]}", size=22, weight=ft.FontWeight.BOLD) # pyright: ignore[reportOptionalSubscript]
        texto_pregunta = ft.Text("¿Qué opción desea?:", size=16)
        
        boton_buscar = ft.FilledButton(
            "Buscar estacionamiento", 
            on_click=lambda e: mostrar_opciones_estacionamiento()
        )
        boton_cerrar_sesion = ft.OutlinedButton("Cerrar Sesión", on_click=lambda e: mostrar_login())

        pagina.add(
            texto_bienvenida, 
            texto_pregunta, 
            boton_buscar, 
            ft.Divider(),
            boton_cerrar_sesion
        )

    #OPCIONES DE ESTACIONAMIENTO
    def mostrar_opciones_estacionamiento():
        pagina.clean()

        titulo_zona = ft.Text("Seleccione una zona", size=22)
        opcion_centro = ft.ElevatedButton("Zona Centro")
        opcion_norte = ft.ElevatedButton("Zona Norte")

        boton_volver = ft.OutlinedButton(
            "Volver al Menú", 
            on_click=lambda e: mostrar_menu_principal()
        )

        pagina.add(titulo_zona, opcion_centro, opcion_norte, boton_volver)

    
    mostrar_login()

ft.app(target=main)