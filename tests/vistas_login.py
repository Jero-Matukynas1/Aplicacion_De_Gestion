import flet as ft

def Menu_Login(page: ft.Page):
    # Centrar
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    
    txt_usuario = ft.TextField(
        label="Usuario", 
        width=300, 
        bgcolor="white24", 
        color="white"
    )
    
    txt_password = ft.TextField(
        label="Contraseña", 
        width=300, 
        password=True, 
        can_reveal_password=True,
        bgcolor="white24",
        color="white"
    )
    

    btn_ingresar = ft.ElevatedButton(
        content=ft.Text("Ingresar", size=16), 
        width=300
    )
    
    btn_registrar = ft.TextButton(
        content=ft.Text("¿No tienes cuenta? Regístrate", color="white")
    )

    conteiner = ft.Container(
        gradient=ft.LinearGradient([
            "#141E30",
            "#243B55"
        ]),
        expand=True,
        
        content=ft.Column(
            controls=[
                ft.Text(
                    "Sistema Gestión De Estacionamiento", 
                    size=32, 
                    weight=ft.FontWeight.BOLD, 
                    color="white",
                    text_align="center"  # type: ignore
                ),
                
               
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

    page.add(conteiner)

ft.app(target=Menu_Login, view=ft.AppView.WEB_BROWSER)