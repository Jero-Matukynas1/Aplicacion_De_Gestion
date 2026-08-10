import flet as ft

def main(page: ft.Page):
    page.bgcolor = ft.Colors.BLUE_GREY_800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.title = "Estacionamiento app"

    # Vista 1: Pantalla principal
    def mostrar_inicio():
        page.clean()  
        
        texto1 = ft.Text("Bienvenido a Estacionamiento App", size=20)
        texto2 = ft.Text("¿Qué opción desea?:")
        boton_buscar = ft.FilledButton(
            "Buscar estacionamiento", 
            on_click=lambda e: mostrar_opciones_estacionamiento()
        )
        
        page.add(texto1, texto2, boton_buscar)

    # Vista 2: buscar estacionamiento
    def mostrar_opciones_estacionamiento():
        page.clean()  
        
        titulo = ft.Text("Seleccione una zona", size=22)
        opcion1 = ft.ElevatedButton("Zona Centro")
        opcion2 = ft.ElevatedButton("Zona Norte")
        
        # Botón para regresar a la vista anterior
        boton_volver = ft.OutlinedButton(
            "Volver", 
            on_click=lambda e: mostrar_inicio()
        )

        page.add(titulo, opcion1, opcion2, boton_volver)

    # Cargar la pantalla de inicio al arrancar la app
    mostrar_inicio()

ft.app(target=main)