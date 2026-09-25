import flet as ft

from tests.vistas_login import VistaLogin 
from tests.vista_estacionamiento import VistaEstacionamiento
from tests.vista_registro import VistaRegistro

def main(page: ft.Page):
    page.title = "Sistema de Gestión"
    page.padding = 0

    def cambiar_ruta(e):
        page.views.clear()

 
        if page.route == "/estacionamiento":
            page.views.append(VistaEstacionamiento(page))
        elif page.route == "/registro":
            page.views.append(VistaRegistro(page))
        else:
            page.views.append(VistaLogin(page))

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = cambiar_ruta
    page.on_view_pop = view_pop
    
    page.views.clear()
    page.views.append(VistaLogin(page))
    page.update()


ft.run(main) # type: ignore