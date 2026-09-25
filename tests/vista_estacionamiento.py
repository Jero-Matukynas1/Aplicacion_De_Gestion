import flet as ft

def VistaEstacionamiento(page: ft.Page):
    rol_usuario = getattr(page, "rol_usuario", "usuario")

    cuadricula_lugares = ft.GridView(expand=True, max_extent=250, child_aspect_ratio=1.0, spacing=15, run_spacing=15)

    def crear_tarjetas(numero, tipo, precio, estado):
        color_estado = "green" if estado == "DISPONIBLE" else "red"
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Text(f"Lugar {numero}", size=20, weight="bold"), # type: ignore
                        ft.Text(f"Tipo: {tipo}"),
                        ft.Text(f"Precio/h: ${precio}"),
                        ft.Text(f"Estado: {estado}", color=color_estado, weight="bold"), # type: ignore
                    ] # type: ignore
                )
            )
        )

    # Lugares de Prueba
    cuadricula_lugares.controls.append(crear_tarjetas("A-1", "Auto", 150, "DISPONIBLE"))
    cuadricula_lugares.controls.append(crear_tarjetas("A-2", "Moto", 80, "RESERVADO"))
    cuadricula_lugares.controls.append(crear_tarjetas("B-1", "Camioneta", 200, "DISPONIBLE"))

    def cerrar_sesion(e):
        # Limpiar el rol al salir
        page.rol_usuario = None  # type: ignore
        page.go("/")

    fila_menu = ft.Row(
        expand=True,
        controls=[
            ft.Container(
                width=200, bgcolor="blueGrey900", padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Menu De Navegacion", color="white", weight="bold"), # type: ignore
                        ft.Divider(height=20, color="transparent"),
                        ft.ElevatedButton("Cerrar Sesión", on_click=cerrar_sesion, bgcolor="red600", color="white") # type: ignore
                    ] # type: ignore
                )
            ),
            ft.Container(
                expand=True, bgcolor="grey100", padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Gestion De Lugares", size=24, weight="bold", color="black"), # type: ignore
                        ft.ElevatedButton(
                            content=ft.Text("+ Añadir Nuevo Lugar", color="white"),
                            bgcolor="blue600", color="white", visible=(rol_usuario == "admin")
                        ), # type: ignore
                        ft.Divider(height=20, color="transparent"),
                        cuadricula_lugares
                    ] # type: ignore
                )
            )
        ]
    )

    return ft.View(
        route="/estacionamiento", 
        padding=0, 
        controls=[fila_menu]
    )