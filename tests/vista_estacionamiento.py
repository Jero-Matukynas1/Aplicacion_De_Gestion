import flet as ft
from database.consultas import obtener_todos_los_lugares, agregar_lugar_estacionamiento, modificar_lugar, eliminar_lugar
# from database.consultas import obtener_lugares, agregar_lugar, modificar_lugar, eliminar_lugar, reservar_lugar

def VistaEstacionamiento(page: ft.Page):
    rol_usuario = getattr(page, "rol_usuario", "usuario") # Asume "usuario" si no hay rol
    
    # ---------------------------------------------------
    # CONTROLES Y CUADRÍCULA
    # ---------------------------------------------------
    cuadricula_lugares = ft.GridView(expand=True, max_extent=250, child_aspect_ratio=0.9, spacing=15, run_spacing=15)
    txt_buscar = ft.TextField(label="Buscar lugar (Ej: Auto)...", width=300, on_change=lambda e: filtrar_lugares(e.control.value))

    # ---------------------------------------------------
    # LÓGICA DE TARJETAS
    # ---------------------------------------------------
    def crear_tarjetas(numero, tipo, precio, estado):
        color_estado = "green" if estado == "DISPONIBLE" else "red"
        acciones = []

        # Controles exclusivos para Administrador
        if rol_usuario == "admin":
            acciones = [
                ft.IconButton(icon=ft.icons.EDIT, tooltip="Modificar", on_click=lambda e: abrir_formulario(numero, tipo, precio, estado)), # type: ignore
                ft.IconButton(icon=ft.icons.DELETE, tooltip="Borrar", icon_color="red", on_click=lambda e: confirmar_borrado(numero)) # type: ignore
            ]
        # Controles exclusivos para Conductor
        elif rol_usuario == "usuario" and estado == "DISPONIBLE":
            acciones = [
                ft.ElevatedButton("Reservar", bgcolor="green600", color="white", on_click=lambda e: confirmar_reserva(numero, precio))
            ]

        return ft.Card(
            content=ft.Container(
                padding=15,
                bgcolor="#1E2328", # Manteniendo el diseño oscuro
                content=ft.Column([
                    ft.Text(f"Lugar {numero}", size=20, weight="bold", color="white"), # type: ignore
                    ft.Text(f"Tipo: {tipo}", color="white70"),
                    ft.Text(f"Precio/h: ${precio}", color="white70"),
                    ft.Text(f"Estado: {estado}", color=color_estado, weight="bold"), # type: ignore
                    ft.Divider(height=10, color="transparent"),
                    ft.Row(acciones, alignment=ft.MainAxisAlignment.END) # type: ignore
                ]) # type: ignore
            )
        )

    def cargar_lugares(filtro=""):
        cuadricula_lugares.controls.clear()
        # SIMULACIÓN: Aquí llamarías a obtener_lugares() de tu base de datos
        datos = obtener_todos_los_lugares()
        
        for id_lugar, num_lugar, tipo, precio, estado in datos:
            if filtro.lower() in tipo.lower() or filtro.lower() in estado.lower() or filtro == "":
                # ATENCIÓN: Ahora le pasas el 'id_lugar' a la tarjeta para que 
                # los botones de Editar/Borrar sepan qué registro atacar en la BD.
                cuadricula_lugares.controls.append(
                    crear_tarjetas(id_lugar, num_lugar, tipo, precio, estado) # type: ignore
                )
        page.update()

    def filtrar_lugares(valor):
        cargar_lugares(valor)

    # ---------------------------------------------------
    # DIÁLOGOS (FORMULARIOS Y CONFIRMACIONES)
    # ---------------------------------------------------
    def abrir_formulario(numero="", tipo="Auto", precio="", estado="DISPONIBLE"):
        es_edicion = bool(numero)
        
        txt_numero = ft.TextField(label="Número de Lugar", value=numero, disabled=es_edicion)
        txt_tipo = ft.Dropdown(label="Tipo de Vehículo", value=tipo, options=[ft.dropdown.Option("Auto"), ft.dropdown.Option("Moto"), ft.dropdown.Option("Camioneta")])
        txt_precio = ft.TextField(label="Precio por hora", value=str(precio))
        drop_estado = ft.Dropdown(label="Estado", value=estado, options=[ft.dropdown.Option("DISPONIBLE"), ft.dropdown.Option("RESERVADO")])

        def guardar(e):
            # Aquí llamas a agregar_lugar() o modificar_lugar() en consultas.py
            dialogo.open = False
            cargar_lugares()
            page.update()

        dialogo = ft.AlertDialog(
            title=ft.Text("Modificar Lugar" if es_edicion else "Añadir Nuevo Lugar"),
            content=ft.Column([txt_numero, txt_tipo, txt_precio, drop_estado], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                ft.ElevatedButton("Guardar", on_click=guardar)
            ]
        )
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    def confirmar_reserva(numero, precio):
        def reservar(e):
            # Aquí llamas a reservar_lugar(numero, page.rol_usuario) en consultas.py
            dialogo.open = False
            cargar_lugares()
            page.update()

        dialogo = ft.AlertDialog(
            title=ft.Text("Confirmar Reserva"),
            content=ft.Text(f"¿Deseas reservar el lugar {numero} por ${precio}/h?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                ft.ElevatedButton("Confirmar", bgcolor="green", color="white", on_click=reservar)
            ]
        )
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()
        
    def confirmar_borrado(numero):
        # Lógica similar a confirmar_reserva, llamando a eliminar_lugar(numero)
        pass

    def cerrar_dialogo(dialogo):
        dialogo.open = False
        page.update()

    # ---------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ---------------------------------------------------
    def cerrar_sesion(e):
        page.rol_usuario = None # type: ignore
        page.go("/")

    fila_menu = ft.Row(
        expand=True,
        controls=[
            # Menú Lateral[cite: 6]
            ft.Container(
                width=200, bgcolor="#263238", padding=20,
                content=ft.Column([
                    ft.Text("Menu De Navegacion", color="white", weight="bold"), # type: ignore
                    ft.Divider(height=20, color="transparent"),
                    ft.ElevatedButton("Cerrar Sesión", bgcolor="#F44336", color="white", on_click=cerrar_sesion)
                ]) # type: ignore
            ),
            # Panel Principal
            ft.Container(
                expand=True, bgcolor="#F5F5F5", padding=20,
                content=ft.Column([
                    ft.Text("Gestion De Lugares", size=24, weight="bold", color="black"), # type: ignore
                    ft.Row([
                        # Botón Add (Solo Admin)
                        ft.ElevatedButton("+ Añadir Nuevo Lugar", bgcolor="blue600", color="white", on_click=lambda e: abrir_formulario(), visible=(rol_usuario == "admin")),
                        # Barra de Búsqueda (Solo Conductor)
                        ft_buscar if rol_usuario == "usuario" else ft.Container() # type: ignore
                    ]),
                    ft.Divider(height=20, color="transparent"),
                    cuadricula_lugares
                ]) # type: ignore
            )
        ]
    )

    # Cargar datos iniciales
    cargar_lugares()

    return ft.View(route="/estacionamiento", padding=0, controls=[fila_menu])