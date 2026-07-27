import flet as ft

def main(page: ft.Page):
    page.title = "Mi Primera App"
    page.add(ft.Text("¡Hola desde Flet!", size=30))

ft.app(target=main)   