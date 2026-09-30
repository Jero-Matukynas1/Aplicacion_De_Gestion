import flet as ft
import database as db


def main(page: ft.Page):
    page.title = "Gestión de Estacionamiento"
    page.window.width = 900
    page.window.height = 650
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    db.init_db()

    # Guardamos el usuario logueado y el estacionamiento elegido, accesibles desde cualquier vista
    sesion = {"usuario": None, "estacionamiento_id": None}

    # Utilidades de UI
    def mostrar_snack(mensaje, error=False):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(mensaje),
                bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
            )
        )

    def cerrar_sesion(e=None):
        sesion["usuario"] = None
        sesion["estacionamiento_id"] = None
        page.navigate("/login")


    # VISTA: LOGIN / REGISTRO
    def vista_login():
        username_field = ft.TextField(label="Usuario", width=300, autofocus=True)
        password_field = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True)

        def hacer_login(e):
            usuario = db.validar_login(username_field.value.strip(), password_field.value)
            if usuario is None:
                mostrar_snack("Usuario o contraseña incorrectos", error=True)
                return
            sesion["usuario"] = dict(usuario)
            page.navigate("/estacionamientos")

        def ir_a_registro(e):
            page.navigate("/registro")

        return ft.View(
            route="/login",
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.LOCAL_PARKING, size=60, color=ft.Colors.BLUE_600),
                            ft.Text("Gestión de Estacionamiento", size=26, weight=ft.FontWeight.BOLD),
                            ft.Container(height=20),
                            username_field,
                            password_field,
                            ft.Container(height=10),
                            ft.Button("Ingresar", width=300, on_click=hacer_login),
                            ft.TextButton("Crear cuenta de conductor", on_click=ir_a_registro),
                            ft.Container(height=10),
                            ft.Text(
                                "Admin por defecto -> usuario: admin | contraseña: admin123",
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                    ),
                )
            ],
        )


    # VISTA: REGISTRO (solo crea usuarios tipo conductor)
    def vista_registro():
        nombre_field = ft.TextField(label="Nombre completo", width=300)
        username_field = ft.TextField(label="Usuario", width=300)
        password_field = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True)

        def registrar(e):
            if not nombre_field.value or not username_field.value or not password_field.value:
                mostrar_snack("Completá todos los campos", error=True)
                return
            ok, msg = db.crear_usuario(
                username_field.value.strip(), password_field.value, nombre_field.value.strip(), "conductor"
            )
            mostrar_snack(msg, error=not ok)
            if ok:
                page.navigate("/login")

        return ft.View(
            route="/registro",
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("Crear cuenta de conductor", size=22, weight=ft.FontWeight.BOLD),
                            ft.Container(height=10),
                            nombre_field,
                            username_field,
                            password_field,
                            ft.Container(height=10),
                            ft.Button("Registrarme", width=300, on_click=registrar),
                            ft.TextButton("Volver al login", on_click=lambda e: page.navigate("/login")),
                        ],
                    ),
                )
            ],
        )

  
    # VISTA: LISTA DE ESTACIONAMIENTOS

    def vista_estacionamientos():
        lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        def ir_a_estacionamiento(est):
            # Guardamos en la sesión CUÁL estacionamiento se eligió; el resto
            # de las vistas (admin/conductor) van a leer este valor para filtrar.
            sesion["estacionamiento_id"] = est["id"]
            if sesion["usuario"]["rol"] == "admin":
                page.navigate("/admin")
            else:
                page.navigate("/conductor")

        def fila_estacionamiento(est):
            total, disponibles = db.contar_lugares(est["id"])
            return ft.Container(
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                # Todo el container es clickeable, no solo un botón
                on_click=lambda e, est=est: ir_a_estacionamiento(est),
                ink=True,  # efecto visual de "click" (ripple)
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(est["nombre"], size=18, weight=ft.FontWeight.BOLD),
                                ft.Text(est["direccion"] or "Sin dirección cargada", size=12, color=ft.Colors.GREY_600),
                                ft.Text(
                                    f"{disponibles} de {total} lugares disponibles",
                                    size=12,
                                    color=ft.Colors.GREEN_600 if disponibles > 0 else ft.Colors.RED_400,
                                ),
                            ]
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400),
                    ],
                ),
            )

        def cargar_estacionamientos():
            lista.controls.clear()
            estacionamientos = db.obtener_estacionamientos()
            if not estacionamientos:
                lista.controls.append(ft.Text("No hay estacionamientos cargados todavía.", color=ft.Colors.GREY_500))
            for est in estacionamientos:
                lista.controls.append(fila_estacionamiento(est))
            page.update()

        cargar_estacionamientos()

        return ft.View(
            route="/estacionamientos",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.AppBar(
                    title=ft.Text(f"Elegí un estacionamiento — {sesion['usuario']['nombre']}"),
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        controls=[
                            ft.Text("Estacionamientos disponibles", size=18, weight=ft.FontWeight.BOLD),
                            lista,
                        ]
                    ),
                ),
            ],
        )

  
    # VISTA: PANEL ADMINISTRADOR
    def vista_admin():
        numero_field = ft.TextField(label="Número de lugar", width=150)
        tipo_dropdown = ft.Dropdown(
            label="Tipo de vehículo",
            width=180,
            options=[
                ft.DropdownOption("auto", "auto"),
                ft.DropdownOption("moto", "moto"),
                ft.DropdownOption("camioneta", "camioneta"),
            ],
        )
        precio_field = ft.TextField(label="Precio por hora", width=150)
        editando_id = {"id": None}  # guarda el id del lugar si estamos editando

        tabla = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        def limpiar_formulario():
            editando_id["id"] = None
            numero_field.value = ""
            tipo_dropdown.value = None
            precio_field.value = ""
            page.update()

        def cargar_lugares():
            tabla.controls.clear()
            lugares = db.obtener_lugares(sesion["estacionamiento_id"])
            if not lugares:
                tabla.controls.append(ft.Text("No hay lugares cargados todavía.", color=ft.Colors.GREY_500))
            for lugar in lugares:
                tabla.controls.append(fila_lugar(lugar))
            page.update()

        def fila_lugar(lugar):
            estado_chip = ft.Container(
                content=ft.Text("Disponible" if lugar["disponible"] else "Ocupado", size=12, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_500 if lugar["disponible"] else ft.Colors.RED_400,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border_radius=20,
            )
            return ft.Container(
                padding=10,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"Lugar #{lugar['numero']}  —  {lugar['tipo_vehiculo']}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"${lugar['precio_hora']:.2f} / hora", size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        ft.Row(
                            controls=[
                                estado_chip,
                                ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=lambda e, l=lugar: cargar_para_editar(l)),
                                ft.IconButton(icon=ft.Icons.DELETE, tooltip="Borrar", icon_color=ft.Colors.RED_400, on_click=lambda e, l=lugar: eliminar(l)),
                            ]
                        ),
                    ],
                ),
            )

        def cargar_para_editar(lugar):
            editando_id["id"] = lugar["id"]
            numero_field.value = str(lugar["numero"])
            tipo_dropdown.value = lugar["tipo_vehiculo"]
            precio_field.value = str(lugar["precio_hora"])
            page.update()

        def eliminar(lugar):
            db.borrar_lugar(lugar["id"])
            mostrar_snack(f"Lugar #{lugar['numero']} eliminado")
            cargar_lugares()

        def guardar(e):
            if not numero_field.value or not tipo_dropdown.value or not precio_field.value:
                mostrar_snack("Completá número, tipo y precio", error=True)
                return
            try:
                numero = int(numero_field.value)
                precio = float(precio_field.value)
            except ValueError:
                mostrar_snack("Número y precio deben ser numéricos", error=True)
                return

            if editando_id["id"] is None:
                ok, msg = db.agregar_lugar(numero, tipo_dropdown.value, precio, sesion["estacionamiento_id"])
            else:
                ok, msg = db.modificar_lugar(editando_id["id"], numero, tipo_dropdown.value, precio, True)

            mostrar_snack(msg, error=not ok)
            if ok:
                limpiar_formulario()
                cargar_lugares()

        cargar_lugares()

        estacionamiento_actual = db.obtener_estacionamiento_por_id(sesion["estacionamiento_id"])

        return ft.View(
            route="/admin",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Volver a estacionamientos",
                        on_click=lambda e: page.navigate("/estacionamientos"),
                    ),
                    title=ft.Text(f"Admin — {estacionamiento_actual['nombre']}"),
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        controls=[
                            ft.Text("Gestionar lugares", size=18, weight=ft.FontWeight.BOLD),
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Container(numero_field, col=3),
                                    ft.Container(tipo_dropdown, col=3),
                                    ft.Container(precio_field, col=3),
                                    ft.Container(
                                        ft.Button("Guardar", icon=ft.Icons.SAVE, on_click=guardar),
                                        col=3,
                                    ),
                                ]
                            ),
                            ft.TextButton("Cancelar edición", on_click=lambda e: limpiar_formulario()),
                            ft.Divider(),
                            ft.Text("Lugares cargados", size=18, weight=ft.FontWeight.BOLD),
                            tabla,
                        ]
                    ),
                ),
            ],
        )

    # VISTA: PANEL CONDUCTOR
    def vista_conductor():
        tipo_filtro = ft.Dropdown(
            label="Filtrar por tipo de vehículo",
            width=250,
            options=[
                ft.DropdownOption("todos", "todos"),
                ft.DropdownOption("auto", "auto"),
                ft.DropdownOption("moto", "moto"),
                ft.DropdownOption("camioneta", "camioneta"),
            ],
            value="todos",
        )

        lista_lugares = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        lista_reservas = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        def cargar_disponibles(e=None):
            lista_lugares.controls.clear()
            lugares = db.obtener_lugares(sesion["estacionamiento_id"], solo_disponibles=True)
            if tipo_filtro.value and tipo_filtro.value != "todos":
                lugares = [l for l in lugares if l["tipo_vehiculo"] == tipo_filtro.value]

            if not lugares:
                lista_lugares.controls.append(ft.Text("No hay lugares disponibles con ese filtro.", color=ft.Colors.GREY_500))

            for lugar in lugares:
                lista_lugares.controls.append(fila_disponible(lugar))
            page.update()

        def fila_disponible(lugar):
            return ft.Container(
                padding=10,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"Lugar #{lugar['numero']}  —  {lugar['tipo_vehiculo']}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"${lugar['precio_hora']:.2f} / hora", size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        ft.Button(
                            "Reservar",
                            icon=ft.Icons.CHECK_CIRCLE,
                            on_click=lambda e, l=lugar: reservar(l),
                        ),
                    ],
                ),
            )

        def reservar(lugar):
            ok, msg = db.reservar_lugar(lugar["id"], sesion["usuario"]["id"])
            mostrar_snack(msg, error=not ok)
            cargar_disponibles()
            cargar_mis_reservas()

        def cargar_mis_reservas(e=None):
            lista_reservas.controls.clear()
            reservas = db.obtener_reservas_usuario(sesion["usuario"]["id"])
            if not reservas:
                lista_reservas.controls.append(ft.Text("Todavía no hiciste ninguna reserva.", color=ft.Colors.GREY_500))
            for r in reservas:
                lista_reservas.controls.append(fila_reserva(r))
            page.update()

        def fila_reserva(r):
            color_estado = {
                "activa": ft.Colors.GREEN_500,
                "finalizada": ft.Colors.GREY_500,
                "cancelada": ft.Colors.RED_400,
            }.get(r["estado"], ft.Colors.GREY_500)

            acciones = []
            if r["estado"] == "activa":
                acciones.append(
                    ft.TextButton("Cancelar", icon=ft.Icons.CANCEL, on_click=lambda e, rid=r["id"]: cancelar(rid))
                )

            return ft.Container(
                padding=10,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"Lugar #{r['numero']} — {r['tipo_vehiculo']}", weight=ft.FontWeight.BOLD),
                                ft.Text(r["estacionamiento_nombre"], size=12, color=ft.Colors.BLUE_600),
                                ft.Text(f"Reservado el {r['fecha_reserva']}", size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        ft.Row(controls=[ft.Text(r["estado"].capitalize(), color=color_estado), *acciones]),
                    ],
                ),
            )

        def cancelar(reserva_id):
            ok, msg = db.cancelar_reserva(reserva_id)
            mostrar_snack(msg, error=not ok)
            cargar_disponibles()
            cargar_mis_reservas()

        cargar_disponibles()
        cargar_mis_reservas()

        estacionamiento_actual = db.obtener_estacionamiento_por_id(sesion["estacionamiento_id"])

        return ft.View(
            route="/conductor",
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Volver a estacionamientos",
                        on_click=lambda e: page.navigate("/estacionamientos"),
                    ),
                    title=ft.Text(f"{estacionamiento_actual['nombre']} — {sesion['usuario']['nombre']}"),
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        controls=[
                            ft.Text("Buscar lugares disponibles", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row(controls=[tipo_filtro, ft.Button("Buscar", icon=ft.Icons.SEARCH, on_click=cargar_disponibles)]),
                            lista_lugares,
                            ft.Divider(),
                            ft.Text("Mis reservas", size=18, weight=ft.FontWeight.BOLD),
                            lista_reservas,
                        ]
                    ),
                ),
            ],
        )

    # RUTEO
    def route_change(e):
        page.views.clear()

        if page.route == "/registro":
            page.views.append(vista_registro())
        elif page.route == "/estacionamientos" and sesion["usuario"]:
            page.views.append(vista_estacionamientos())
        elif (
            page.route == "/admin"
            and sesion["usuario"]
            and sesion["usuario"]["rol"] == "admin"
            and sesion["estacionamiento_id"] is not None
        ):
            page.views.append(vista_admin())
        elif (
            page.route == "/conductor"
            and sesion["usuario"]
            and sesion["usuario"]["rol"] == "conductor"
            and sesion["estacionamiento_id"] is not None
        ):
            page.views.append(vista_conductor())
        else:
            # cualquier ruta desconocida, o acceso sin sesión, vuelve al login
            page.views.append(vista_login())

        page.update()

    page.on_route_change = route_change

    # Renderiza la vista inicial
    if page.route == "/":
        page.route = "/login"
    route_change(None)


if __name__ == "__main__":
    ft.run(main)