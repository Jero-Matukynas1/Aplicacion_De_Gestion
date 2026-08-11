import flet as ft

def Menu_Estacionaiento(page: ft.Page):
    page.title = "Panel de Administración - Estacionamiento"
    page.padding = 0

    rol_usuario = "admin"
    #Crear las Grillas
    cuadricula_lugares = ft.GridView(
        expand=True,
        max_extent=250,
        child_aspect_ratio=1.0,
        spacing= 15,
        run_spacing= 15,
    )
    #Funcion crea la parte visual de las tarjetas <
    def crear_tarjetas(numero, tipo, precio, estado):
        color_estado = "green" if estado == "DISPONIBLE" else "red"

        return ft.Card(
            content= ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.Text(f"Lugar {numero}", size=20, weight="bold"), # type: ignore
                        ft.Text(f"Tipo: {tipo}"),
                        ft.Text(f"Precio/h: ${precio}"),
                        ft.Text(f"Estado: {estado}", color= color_estado, weight="bold"), # type: ignore
                    ] # type: ignore
                )
            )
        )
    #lugares de Prueba
    cuadricula_lugares.controls.append(crear_tarjetas("A-1", "Auto", 150, "DISPONIBLE"))
    cuadricula_lugares.controls.append(crear_tarjetas("A-2", "Moto", 80, "RESERVADO"))
    cuadricula_lugares.controls.append(crear_tarjetas("B-1", "Camioneta", 200, "DISPONIBLE"))
    fila_menu = ft.Row(
        controls=[
            ft.Container(
                width= 200,
                bgcolor="blueGrey900",
                padding= 20,
                content=ft.Column(
                    controls=[
                        ft.Text("Menu De Navegacion", color="white", weight="bold"), # type: ignore
                        ft.Divider(height=20, color="transparent"),
                        #Aca abajo se le puede seguir poniendo botones o cosas al menu lateral izquierdo 
                        
                    ] # type: ignore
                )
            ),
            #Panel Principal donde se muestan lo lugares, etc
            ft.Container(
                expand=True,
                bgcolor="grey100",
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Gestion De Lugares", size=24, weight="blod", color="black"), # type: ignore

                        ft.ElevatedButton(
                            content=ft.Text("+ Añadir Nuevo Lugar", color="white"),
                            bgcolor="blue600",
                            color="white",
                            visible=(rol_usuario == "admin")
                        ),
                        ft.Divider(height=20, color="transparent"),

                        cuadricula_lugares
                    ] # type: ignore
                )
            )
        ],
        expand=True 
    )
    page.add(fila_menu)

ft.app(target=Menu_Estacionaiento, view=ft.AppView.WEB_BROWSER)