import flet as ft
from database.consultas import verificar_credenciales

def VistaLogin(page: ft.Page):
    txt_usuario = ft.TextField(label="Usuario", width=300, bgcolor="white24", color="white")
    txt_password = ft.TextField(label="Contraseña", width=300, password=True, can_reveal_password=True, bgcolor="white24", color="white")

    def intentar_login(e):
        rol = verificar_credenciales(txt_usuario.value, txt_password.value)
        
        if rol:
            # Asignación rol
            page.rol_usuario = rol  # type: ignore
            page.go("/estacionamiento")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Usuario o contraseña incorrectos"), bgcolor="red") # type: ignore
            page.snack_bar.open = True # type: ignore
            page.update()

    btn_ingresar = ft.ElevatedButton(content=ft.Text("Ingresar", size=16), width=300, on_click=intentar_login) # type: ignore
    btn_registrar = ft.TextButton(
        content=ft.Text("¿No tienes cuenta? Regístrate", color="white"),
        #carga la nueva vista
        on_click=lambda e: page.go("/registro") 
    )

    return ft.View(
        route="/",
        padding=0,
        controls=[
            ft.Container(
                gradient=ft.LinearGradient(["#141E30", "#243B55"]),
                expand=True,
                content=ft.Column(
                    controls=[
                        ft.Text("Sistema Gestión De Estacionamiento", size=32, weight=ft.FontWeight.BOLD, color="white", text_align="center"), # type: ignore
                        ft.Divider(height=10, color="transparent"),
                        ft.Text("Iniciar Sesión", size=20, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Divider(height=25, color="transparent"),
                        txt_usuario,
                        txt_password,
                        ft.Divider(height=20, color="transparent"),
                        btn_ingresar,
                        btn_registrar
                    ], # type: ignore
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        ]
    )