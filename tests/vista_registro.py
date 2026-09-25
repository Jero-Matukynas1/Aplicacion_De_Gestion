import flet as ft
from database.consultas import registrar_usuario

def VistaRegistro(page: ft.Page):
    txt_usuario = ft.TextField(label="Nuevo Usuario", width=300, bgcolor="white24", color="white")
    txt_password = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True, bgcolor="white24", color="white")
    
    # Menú desplegable, mateo no se si hacer q el usuario elija el rol o el sistema se lo de
    dropdown_rol = ft.Dropdown(
        width=300,
        options=[ft.dropdown.Option("usuario"), ft.dropdown.Option("admin")],
        value="usuario",
        bgcolor="white24", color="white"
    )

    def intentar_registro(e):
        if registrar_usuario(txt_usuario.value, txt_password.value, dropdown_rol.value): # type: ignore
            page.snack_bar = ft.SnackBar(ft.Text("Registro exitoso"), bgcolor="green") # type: ignore
            page.snack_bar.open = True # type: ignore
            page.go("/") # Vuelve al login al terminar
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error al registrar (El usuario podría ya existir)"), bgcolor="red") # type: ignore
            page.snack_bar.open = True # type: ignore
        page.update()

    btn_registrar = ft.ElevatedButton(content=ft.Text("Crear Cuenta", size=16), width=300, on_click=intentar_registro)
    
   
    btn_volver = ft.TextButton(content=ft.Text("Volver al Login", color="white"), on_click=lambda e: page.go("/"))

    conteiner = ft.Container(
        gradient=ft.LinearGradient(["#141E30", "#243B55"]),
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Registro de Usuario", size=32, weight="bold", color="white"), # type: ignore
                ft.Divider(height=25, color="transparent"),
                txt_usuario,
                txt_password,
                dropdown_rol,
                ft.Divider(height=20, color="transparent"),
                btn_registrar,
                btn_volver
            ], # type: ignore
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

    return ft.View(route="/registro", padding=0, controls=[conteiner])