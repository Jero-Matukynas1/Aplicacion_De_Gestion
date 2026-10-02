import flet as ft
import database as db


def main(page: ft.Page):
    page.title = "Gestión de Estacionamiento"
    page.window.width = 900
    page.window.height = 650
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    try:
        db.init_db()
        db.preparar_tabla_facturacion()
        db.preparar_tabla_usuarios()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

    # Guardamos el usuario logueado y el estacionamiento elegido, accesibles desde cualquier vista
    sesion = {"usuario": None, "estacionamiento_id": None}

    # Utilidades de UI
    def mostrar_snack(mensaje, error=False):
        snack = ft.SnackBar(
            content=ft.Text(mensaje),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_400,
            open=True,
        )
        page.snack_bar = snack
        try:
            page.overlay.append(snack)
        except Exception:
            pass
        page.update()
        
        
    def cerrar_sesion(e=None):
        sesion["usuario"] = None
        sesion["estacionamiento_id"] = None
        page.navigate("/login")


    # VISTA: LOGIN / REGISTRO
    def vista_login():
        username_field = ft.TextField(label="Usuario", width=300, autofocus=True)
        password_field = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True)

        def hacer_login(e):
            try:
                usuario = db.validar_login(username_field.value.strip(), password_field.value)
                if usuario is None:
                    mostrar_snack("Usuario o contraseña incorrectos", error=True)
                    return
                
                # MEJORA: Seguridad. Purgamos la contraseña antes de guardar en memoria de sesión
                usuario_seguro = dict(usuario)
                usuario_seguro.pop("password", None) 
                
                sesion["usuario"] = usuario_seguro
                page.navigate("/estacionamientos")
            except Exception as ex:
                mostrar_snack("Error de conexión con la base de datos.", error=True)

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
    # VISTA: REGISTRO DE USUARIOS
    def vista_registro():
        nombre_field = ft.TextField(label="Nombre completo", width=300)
        usuario_field = ft.TextField(label="Nombre de usuario", width=300)
        email_field = ft.TextField(label="Correo electrónico (Email)", width=300)
        dni_field = ft.TextField(
            label="DNI (8 dígitos)", 
            width=300, 
            max_length=8,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        clave_field = ft.TextField(label="Contraseña (mínimo 8 caracteres)", password=True, can_reveal_password=True, width=300)

        def procesar_registro(e):
            ok, msg = db.registrar_usuario(
                nombre=nombre_field.value,
                usuario=usuario_field.value,
                clave=clave_field.value,
                email=email_field.value,
                dni=dni_field.value,
                rol="conductor"
            )
            mostrar_snack(msg, error=not ok)
            if ok:
                page.navigate("/login")

        return ft.View(
            route="/registro",
            controls=[
                ft.Container(
                    alignment=ft.Alignment(0, 0),  # Centrado universal compatible con todas las versiones
                    expand=True,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15,
                        controls=[
                            ft.Text("Crear nueva cuenta", size=24, weight=ft.FontWeight.BOLD),
                            nombre_field,
                            usuario_field,
                            email_field,
                            dni_field,
                            clave_field,
                            ft.Button("Registrarse", on_click=procesar_registro, width=300),
                            ft.TextButton("¿Ya tenés cuenta? Iniciá sesión", on_click=lambda e: page.navigate("/login")),
                        ],
                    ),
                )
            ],
        )
  
    # VISTA: LISTA DE ESTACIONAMIENTOS
    def vista_estacionamientos():
        lista = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        def ir_a_estacionamiento(est):
            sesion["estacionamiento_id"] = est["id"]
            if sesion["usuario"]["rol"] == "admin":
                page.navigate("/admin")
            else:
                page.navigate("/conductor")

        def fila_estacionamiento(est):
            try:
                total, disponibles = db.contar_lugares(est["id"])
            except Exception:
                total, disponibles = 0, 0

            return ft.Container(
                padding=15,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                on_click=lambda e, est=est: ir_a_estacionamiento(est),
                ink=True,
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
            try:
                estacionamientos = db.obtener_estacionamientos()
                if not estacionamientos:
                    lista.controls.append(ft.Text("No hay estacionamientos cargados todavía.", color=ft.Colors.GREY_500))
                for est in estacionamientos:
                    lista.controls.append(fila_estacionamiento(est))
            except Exception:
                lista.controls.append(ft.Text("Error al cargar estacionamientos.", color=ft.Colors.RED_400))
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
    # VISTA: PANEL ADMINISTRADOR CON FACTURACIÓN E HISTORIAL DE PAGOS
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
        editando_id = {"id": None}

        tabla_lugares = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        tabla_pagos = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        # Módulo de métricas financieras
        txt_hoy = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
        txt_mes = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
        txt_total = ft.Text("$0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700)

        def actualizar_recaudacion():
            try:
                resumen = db.obtener_resumen_recaudacion(sesion["estacionamiento_id"])
                txt_hoy.value = f"${resumen['hoy']:.2f}"
                txt_mes.value = f"${resumen['mes']:.2f}"
                txt_total.value = f"${resumen['total']:.2f}"
            except Exception:
                pass

        def cargar_historial_pagos():
            tabla_pagos.controls.clear()
            try:
                pagos = db.obtener_historial_pagos(sesion["estacionamiento_id"])
                if not pagos:
                    tabla_pagos.controls.append(ft.Text("No hay cobros registrados aún.", color=ft.Colors.GREY_500))
                for p in pagos:
                    # p -> (id, cliente, lugar_num, tipo, fecha_inicio, fecha_fin, monto)
                    tabla_pagos.controls.append(
                        ft.Container(
                            padding=10,
                            border=ft.Border.all(1, ft.Colors.GREY_300),
                            border_radius=8,
                            bgcolor=ft.Colors.GREY_50,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(f"Cliente: {p[1]} — Lugar #{p[2]} ({p[3]})", weight=ft.FontWeight.BOLD),
                                            ft.Text(f"Salida: {p[5]}", size=12, color=ft.Colors.GREY_600),
                                        ]
                                    ),
                                    ft.Text(f"+${p[6]:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                                ],
                            ),
                        )
                    )
            except Exception:
                tabla_pagos.controls.append(ft.Text("Error al cargar el historial de pagos.", color=ft.Colors.RED_400))

        def limpiar_formulario():
            editando_id["id"] = None
            numero_field.value = ""
            tipo_dropdown.value = None
            precio_field.value = ""
            page.update()

        def cargar_lugares():
            tabla_lugares.controls.clear()
            try:
                lugares = db.obtener_lugares(sesion["estacionamiento_id"])
                if not lugares:
                    tabla_lugares.controls.append(ft.Text("No hay lugares cargados todavía.", color=ft.Colors.GREY_500))
                for lugar in lugares:
                    tabla_lugares.controls.append(fila_lugar(lugar))
            except Exception:
                tabla_lugares.controls.append(ft.Text("Error al cargar los lugares.", color=ft.Colors.RED_400))
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
            try:
                db.borrar_lugar(lugar["id"])
                mostrar_snack(f"Lugar #{lugar['numero']} eliminado")
                cargar_lugares()
            except Exception:
                mostrar_snack("Error al eliminar el lugar.", error=True)

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

            try:
                if editando_id["id"] is None:
                    ok, msg = db.agregar_lugar(numero, tipo_dropdown.value, precio, sesion["estacionamiento_id"])
                else:
                    ok, msg = db.modificar_lugar(editando_id["id"], numero, tipo_dropdown.value, precio, True)

                mostrar_snack(msg, error=not ok)
                if ok:
                    limpiar_formulario()
                    cargar_lugares()
            except Exception:
                mostrar_snack("Error al procesar la solicitud en la base de datos.", error=True)

        # Cargas iniciales
        cargar_lugares()
        actualizar_recaudacion()
        cargar_historial_pagos()

        try:
            estacionamiento_actual = db.obtener_estacionamiento_por_id(sesion["estacionamiento_id"])
            nombre_est = estacionamiento_actual['nombre']
        except Exception:
            nombre_est = "Estacionamiento"

        # Tarjeta resumen de cobros
        panel_recaudacion = ft.Container(
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            content=ft.Column(
                controls=[
                    ft.Text("Resumen de Recaudación", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        controls=[
                            ft.Column(controls=[ft.Text("Hoy", size=12, color=ft.Colors.GREY_600), txt_hoy]),
                            ft.Column(controls=[ft.Text("Este Mes", size=12, color=ft.Colors.GREY_600), txt_mes]),
                            ft.Column(controls=[ft.Text("Total Histórico", size=12, color=ft.Colors.GREY_600), txt_total]),
                        ],
                    ),
                ]
            ),
        )

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
                    title=ft.Text(f"Admin — {nombre_est}"),
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        controls=[
                            panel_recaudacion,
                            ft.Divider(),
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
                            tabla_lugares,
                            ft.Divider(),
                            ft.Text("Historial de Pagos y Salidas", size=18, weight=ft.FontWeight.BOLD),
                            tabla_pagos,
                        ]
                    ),
                ),
            ],
        )

    # VISTA: PANEL CONDUCTOR
    def vista_conductor():
        lista_lugares = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        lista_reservas = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        # 1. Creamos el Dropdown SIN 'on_change' dentro para evitar el crash de __init__
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

        # 2. Función de carga y filtrado de disponibilidad
        # Función de carga y filtrado de disponibilidad
        def cargar_disponibles(e=None):
            lista_lugares.controls.clear()

            # Leemos directamente el valor seleccionado en el Dropdown tipo_filtro
            valor_str = str(tipo_filtro.value).strip().lower() if tipo_filtro.value else "todos"

            try:
                lugares = db.obtener_lugares(sesion["estacionamiento_id"], solo_disponibles=True)

                if valor_str != "todos":
                    lugares_filtrados = []
                    for l in lugares:
                        dict_l = dict(l)
                        tipo_v = str(dict_l.get("tipo_vehiculo", "")).strip().lower()
                        if tipo_v == valor_str:
                            lugares_filtrados.append(l)
                    lugares = lugares_filtrados

                if not lugares:
                    lista_lugares.controls.append(
                        ft.Text("No hay lugares disponibles con ese filtro.", color=ft.Colors.GREY_500)
                    )
                else:
                    for lugar in lugares:
                        lista_lugares.controls.append(fila_disponible(lugar))
            except Exception:
                lista_lugares.controls.append(
                    ft.Text("Error al cargar disponibilidad.", color=ft.Colors.RED_400)
                )

            page.update()

        # Enlace externo de evento
        tipo_filtro.on_change = cargar_disponibles
        
        def finalizar_y_cobrar(reserva_id):
            try:
                ok, msg = db.finalizar_reserva_y_cobrar(reserva_id)
                mostrar_snack(msg, error=not ok)
                cargar_disponibles()
                cargar_mis_reservas()
            except Exception:
                mostrar_snack("Error al finalizar la estadía.", error=True)

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
            try:
                ok, msg = db.reservar_lugar(lugar["id"], sesion["usuario"]["id"])
                mostrar_snack(msg, error=not ok)
                cargar_disponibles()
                cargar_mis_reservas()
            except Exception:
                mostrar_snack("Error procesando la reserva.", error=True)

        def cargar_mis_reservas(e=None):
            lista_reservas.controls.clear()
            try:
                reservas = db.obtener_reservas_usuario(sesion["usuario"]["id"])
                if not reservas:
                    lista_reservas.controls.append(ft.Text("Todavía no hiciste ninguna reserva.", color=ft.Colors.GREY_500))
                else:
                    for r in reservas:
                        lista_reservas.controls.append(fila_reserva(r))
            except Exception as ex:
                lista_reservas.controls.append(ft.Text(f"Error cargando el historial: {ex}", color=ft.Colors.RED_400))
            page.update()

        def fila_reserva(r):
            dict_r = dict(r) if not isinstance(r, dict) else r
            estado = str(dict_r.get("estado", "")).lower()

            color_estado = {
                "activa": ft.Colors.GREEN_500,
                "finalizada": ft.Colors.BLUE_600,
                "cancelada": ft.Colors.RED_400,
            }.get(estado, ft.Colors.GREY_500)

            acciones = []
            if estado == "activa":
                acciones.extend([
                    ft.Button(
                        "Finalizar y Pagar",
                        icon=ft.Icons.ATTACH_MONEY,
                        on_click=lambda e, rid=dict_r["id"]: finalizar_y_cobrar(rid),
                    ),
                    ft.TextButton("Cancelar", icon=ft.Icons.CANCEL, on_click=lambda e, rid=dict_r["id"]: cancelar(rid)),
                ])

            monto = dict_r.get("monto_total", 0.0)
            info_monto = f" — Total cobrado: ${float(monto):.2f}" if estado == "finalizada" and monto else ""

            return ft.Container(
                padding=10,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(f"Lugar #{dict_r.get('numero', '')} — {dict_r.get('tipo_vehiculo', '')}", weight=ft.FontWeight.BOLD),
                                ft.Text(dict_r.get("estacionamiento_nombre", ""), size=12, color=ft.Colors.BLUE_600),
                                ft.Text(f"Inicio: {dict_r.get('fecha_reserva', '')}{info_monto}", size=12, color=ft.Colors.GREY_600),
                            ]
                        ),
                        ft.Row(controls=[ft.Text(estado.capitalize(), color=color_estado), *acciones]),
                    ],
                ),
            )

        def cancelar(reserva_id):
            try:
                ok, msg = db.cancelar_reserva(reserva_id)
                mostrar_snack(msg, error=not ok)
                cargar_disponibles()
                cargar_mis_reservas()
            except Exception:
                mostrar_snack("Error al cancelar la reserva.", error=True)

        cargar_disponibles()
        cargar_mis_reservas()

        try:
            estacionamiento_actual = db.obtener_estacionamiento_por_id(sesion["estacionamiento_id"])
            nombre_est = estacionamiento_actual['nombre']
        except Exception:
            nombre_est = "Estacionamiento"

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
                    title=ft.Text(f"{nombre_est} — {sesion['usuario']['nombre']}"),
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    actions=[ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Cerrar sesión", on_click=cerrar_sesion)],
                ),
                ft.Container(
                    padding=20,
                    content=ft.Column(
                        controls=[
                            ft.Text("Buscar lugares disponibles", size=18, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                controls=[
                                    tipo_filtro,
                                    ft.Button("Filtrar", icon=ft.Icons.FILTER_ALT, on_click=cargar_disponibles)
                                ]
                            ),
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

        # MEJORA: Protección de rutas robusta. Redirige según estado de sesión y rol
        ruta = page.route

        if ruta == "/registro":
            page.views.append(vista_registro())
        elif sesion["usuario"] is None:
            # Si intenta acceder a cualquier vista sin loguearse, forzar el login
            page.views.append(vista_login())
        elif ruta == "/estacionamientos":
            page.views.append(vista_estacionamientos())
        elif ruta == "/admin" and sesion["usuario"].get("rol") == "admin" and sesion["estacionamiento_id"] is not None:
            page.views.append(vista_admin())
        elif ruta == "/conductor" and sesion["usuario"].get("rol") == "conductor" and sesion["estacionamiento_id"] is not None:
            page.views.append(vista_conductor())
        else:
            # Si está logueado pero intenta ingresar a una ruta no permitida por su rol, o sin seleccionar estacionamiento
            page.views.append(vista_estacionamientos())

        page.update()

    page.on_route_change = route_change

    # Renderiza la vista inicial
    if page.route == "/":
        page.route = "/login"
    route_change(None)


if __name__ == "__main__":
    # MEJORA: Uso de ft.app(target=main), estándar en las versiones actuales de Flet
    ft.run(main)