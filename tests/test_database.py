import os
import pathlib
import sqlite3
import tempfile
import unittest
 
import database as db
 
EXTENSIONES_DB = (".db", ".sqlite", ".sqlite3")
 
 
# --------------------------------------------------------------------------- #
# Utilidades para aislar la base de datos
# --------------------------------------------------------------------------- #
def _redirigir_rutas_db(carpeta_tmp):
    """Cambia toda constante de ruta a un .db dentro de `db` por una ruta
    temporal. Devuelve una función que restaura los valores originales."""
    nueva_ruta = os.path.join(carpeta_tmp, "test_estacionamiento.db")
    originales = {}
    for nombre, valor in list(vars(db).items()):
        if isinstance(valor, (str, os.PathLike)) and str(valor).endswith(EXTENSIONES_DB):
            originales[nombre] = valor
            setattr(db, nombre, pathlib.Path(nueva_ruta) if isinstance(valor, os.PathLike) else nueva_ruta)
 
    def restaurar():
        for nombre, valor in originales.items():
            setattr(db, nombre, valor)
 
    return restaurar
 
 
def _archivos_db(carpeta):
    encontrados = []
    for raiz, _, archivos in os.walk(carpeta):
        for a in archivos:
            if a.endswith(EXTENSIONES_DB):
                encontrados.append(os.path.join(raiz, a))
    return encontrados
 
 
def _texto_aparece_en_db(carpeta, texto):
    """True si `texto` aparece en alguna celda de alguna tabla de la base."""
    for ruta in _archivos_db(carpeta):
        con = sqlite3.connect(ruta)
        try:
            tablas = [
                r[0]
                for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            for tabla in tablas:
                for fila in con.execute(f'SELECT * FROM "{tabla}"'):
                    for celda in fila:
                        if isinstance(celda, str) and texto in celda:
                            return True
                        if isinstance(celda, bytes) and texto.encode() in celda:
                            return True
        finally:
            con.close()
    return False
 
 
class BaseTest(unittest.TestCase):
    """Crea una base temporal limpia por cada test y ofrece helpers."""
 
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)          # se ejecuta último
        cwd_original = os.getcwd()
        os.chdir(self._tmp.name)                    # cubre rutas relativas ("estacionamiento.db")
        self.addCleanup(os.chdir, cwd_original)
        self.addCleanup(_redirigir_rutas_db(self._tmp.name))  # cubre constantes del módulo
 
        db.init_db()
 
        if not _archivos_db(self._tmp.name):
            raise RuntimeError(
                "No se pudo redirigir la base de datos a un archivo temporal "
                "(los tests habrían tocado tu base real). Revisá cómo database.py "
                "arma la ruta del .db y ajustá _redirigir_rutas_db()."
            )
 
    # -- helpers ----------------------------------------------------------- #
    def est_id(self):
        ests = db.obtener_estacionamientos()
        if not ests:
            self.skipTest("init_db() no crea ningún estacionamiento; agregá uno para correr este test.")
        return ests[0]["id"]
 
    def crear_conductor(self, username="juan", password="clave123", nombre="Juan Pérez"):
        ok, msg = db.crear_usuario(username, password, nombre, "conductor")
        self.assertTrue(ok, msg)
        return dict(db.validar_login(username, password))["id"]
 
    def crear_lugar(self, numero=901, tipo="auto", precio=100.0, est=None):
        est = est if est is not None else self.est_id()
        ok, msg = db.agregar_lugar(numero, tipo, precio, est)
        self.assertTrue(ok, msg)
        return self.buscar_lugar(numero, est)
 
    def buscar_lugar(self, numero, est=None):
        est = est if est is not None else self.est_id()
        for l in db.obtener_lugares(est):
            if l["numero"] == numero:
                return dict(l)
        self.fail(f"No se encontró el lugar #{numero} en el estacionamiento {est}")
 
    def lugar_por_id(self, lugar_id):
        for l in db.obtener_lugares(self.est_id()):
            if l["id"] == lugar_id:
                return dict(l)
        return None
 
    def reservas_de(self, usuario_id):
        return [dict(r) for r in db.obtener_reservas_usuario(usuario_id)]
 
 
# --------------------------------------------------------------------------- #
# USUARIOS / LOGIN
# --------------------------------------------------------------------------- #
class TestUsuarios(BaseTest):
    def test_admin_por_defecto_puede_ingresar(self):
        u = db.validar_login("admin", "admin123")
        self.assertIsNotNone(u)
        u = dict(u)
        for clave in ("id", "nombre", "rol"):
            self.assertIn(clave, u)
        self.assertEqual(u["rol"], "admin")
 
    def test_login_con_password_incorrecta_devuelve_none(self):
        self.assertIsNone(db.validar_login("admin", "incorrecta"))
 
    def test_login_con_usuario_inexistente_devuelve_none(self):
        self.assertIsNone(db.validar_login("nadie", "admin123"))
 
    def test_login_distingue_mayusculas_en_la_password(self):
        self.assertIsNone(db.validar_login("admin", "ADMIN123"))
 
    def test_login_resiste_inyeccion_sql(self):
        for usuario, clave in [
            ("' OR '1'='1' --", "x"),
            ("admin' --", "x"),
            ("admin", "' OR '1'='1"),
        ]:
            with self.subTest(usuario=usuario, clave=clave):
                self.assertIsNone(db.validar_login(usuario, clave))
 
    def test_registro_de_conductor_ok_y_luego_puede_ingresar(self):
        ok, msg = db.crear_usuario("juan", "clave123", "Juan Pérez", "conductor")
        self.assertTrue(ok, msg)
        u = db.validar_login("juan", "clave123")
        self.assertIsNotNone(u)
        self.assertEqual(dict(u)["rol"], "conductor")
        self.assertEqual(dict(u)["nombre"], "Juan Pérez")
 
    def test_registro_con_usuario_duplicado_es_rechazado(self):
        self.assertTrue(db.crear_usuario("juan", "clave123", "Juan", "conductor")[0])
        ok, msg = db.crear_usuario("juan", "otra", "Otro Juan", "conductor")
        self.assertFalse(ok)
        self.assertTrue(msg)  # la interfaz muestra este mensaje
 
    def test_registro_duplicado_no_pisa_la_password_original(self):
        db.crear_usuario("juan", "clave123", "Juan", "conductor")
        db.crear_usuario("juan", "hackeada", "Impostor", "conductor")
        self.assertIsNotNone(db.validar_login("juan", "clave123"))
        self.assertIsNone(db.validar_login("juan", "hackeada"))
 
    def test_la_password_no_se_guarda_en_texto_plano(self):
        secreto = "P4ssw0rd-Unica-Xyz!"
        db.crear_usuario("maria", secreto, "María", "conductor")
        self.assertFalse(
            _texto_aparece_en_db(self._tmp.name, secreto),
            "La contraseña aparece en texto plano en la base: usá un hash (bcrypt/argon2/pbkdf2).",
        )
 
 
# --------------------------------------------------------------------------- #
# ESTACIONAMIENTOS
# --------------------------------------------------------------------------- #
class TestEstacionamientos(BaseTest):
    def test_contar_lugares_refleja_altas_y_reservas(self):
        est = self.est_id()
        total0, disp0 = tuple(db.contar_lugares(est))
 
        lugar = self.crear_lugar(901)
        self.assertEqual(tuple(db.contar_lugares(est)), (total0 + 1, disp0 + 1))
 
        uid = self.crear_conductor()
        db.reservar_lugar(lugar["id"], uid)
        self.assertEqual(tuple(db.contar_lugares(est)), (total0 + 1, disp0))
 
    def test_disponibles_nunca_supera_al_total(self):
        est = self.est_id()
        self.crear_lugar(901)
        total, disp = tuple(db.contar_lugares(est))
        self.assertGreaterEqual(disp, 0)
        self.assertLessEqual(disp, total)
 
    def test_obtener_estacionamiento_por_id_devuelve_nombre(self):
        est = db.obtener_estacionamientos()[0] if db.obtener_estacionamientos() else self.skipTest("sin estacionamientos")
        fila = db.obtener_estacionamiento_por_id(est["id"])
        self.assertEqual(fila["nombre"], est["nombre"])
 
    def test_obtener_estacionamiento_inexistente_devuelve_none(self):
        # La vista admin/conductor hace estacionamiento_actual['nombre']: con None se rompería.
        self.assertIsNone(db.obtener_estacionamiento_por_id(999999))
 
 
# --------------------------------------------------------------------------- #
# LUGARES (CRUD)
# --------------------------------------------------------------------------- #
class TestLugares(BaseTest):
    def test_agregar_lugar_y_leer_sus_campos(self):
        lugar = self.crear_lugar(901, "camioneta", 150.5)
        self.assertEqual(lugar["numero"], 901)
        self.assertEqual(lugar["tipo_vehiculo"], "camioneta")
        self.assertAlmostEqual(lugar["precio_hora"], 150.5)
        self.assertTrue(lugar["disponible"])
 
    def test_modificar_lugar_actualiza_los_datos(self):
        lugar = self.crear_lugar(901, "auto", 100.0)
        ok, msg = db.modificar_lugar(lugar["id"], 902, "moto", 80.0, True)
        self.assertTrue(ok, msg)
        actualizado = self.lugar_por_id(lugar["id"])
        self.assertEqual(actualizado["numero"], 902)
        self.assertEqual(actualizado["tipo_vehiculo"], "moto")
        self.assertAlmostEqual(actualizado["precio_hora"], 80.0)
 
    def test_modificar_lugar_respeta_el_flag_disponible(self):
        lugar = self.crear_lugar(901)
        db.modificar_lugar(lugar["id"], 901, "auto", 100.0, False)
        self.assertFalse(self.lugar_por_id(lugar["id"])["disponible"])
 
    def test_borrar_lugar_lo_quita_del_listado(self):
        lugar = self.crear_lugar(901)
        db.borrar_lugar(lugar["id"])
        self.assertIsNone(self.lugar_por_id(lugar["id"]))
 
    def test_borrar_lugar_inexistente_no_lanza_excepcion(self):
        db.borrar_lugar(999999)
 
    def test_solo_disponibles_excluye_los_reservados(self):
        est = self.est_id()
        libre = self.crear_lugar(901)
        ocupado = self.crear_lugar(902)
        db.reservar_lugar(ocupado["id"], self.crear_conductor())
 
        ids_todos = {l["id"] for l in db.obtener_lugares(est)}
        ids_libres = {l["id"] for l in db.obtener_lugares(est, solo_disponibles=True)}
 
        self.assertIn(ocupado["id"], ids_todos)
        self.assertIn(libre["id"], ids_libres)
        self.assertNotIn(ocupado["id"], ids_libres)
 
    def test_los_lugares_de_un_estacionamiento_no_aparecen_en_otro(self):
        ests = db.obtener_estacionamientos()
        if len(ests) < 2:
            self.skipTest("Se necesitan al menos 2 estacionamientos.")
        a, b = ests[0]["id"], ests[1]["id"]
        self.crear_lugar(901, est=a)
        self.assertNotIn(901, [l["numero"] for l in db.obtener_lugares(b)])
 
    def test_borrar_lugar_con_reserva_activa_no_rompe_las_consultas(self):
        lugar = self.crear_lugar(901)
        uid = self.crear_conductor()
        db.reservar_lugar(lugar["id"], uid)
        db.borrar_lugar(lugar["id"])            # no debería lanzar excepción
        self.reservas_de(uid)                   # la vista "Mis reservas" tampoco debería romperse
 
 
# --------------------------------------------------------------------------- #
# RESERVAS
# --------------------------------------------------------------------------- #
class TestReservas(BaseTest):
    def test_reservar_ok_ocupa_el_lugar_y_crea_reserva_activa(self):
        lugar = self.crear_lugar(901)
        uid = self.crear_conductor()
 
        ok, msg = db.reservar_lugar(lugar["id"], uid)
        self.assertTrue(ok, msg)
        self.assertFalse(self.lugar_por_id(lugar["id"])["disponible"])
 
        reservas = self.reservas_de(uid)
        self.assertEqual(len(reservas), 1)
        r = reservas[0]
        for clave in ("id", "numero", "tipo_vehiculo", "estacionamiento_nombre", "fecha_reserva", "estado"):
            self.assertIn(clave, r)
        self.assertEqual(r["estado"], "activa")
        self.assertEqual(r["numero"], 901)
 
    def test_no_se_puede_reservar_un_lugar_ya_ocupado(self):
        lugar = self.crear_lugar(901)
        u1 = self.crear_conductor("ana", "clave1", "Ana")
        u2 = self.crear_conductor("beto", "clave2", "Beto")
 
        self.assertTrue(db.reservar_lugar(lugar["id"], u1)[0])
        ok, msg = db.reservar_lugar(lugar["id"], u2)
 
        self.assertFalse(ok)
        self.assertTrue(msg)
        self.assertEqual(self.reservas_de(u2), [])
 
    def test_el_mismo_usuario_no_puede_reservar_dos_veces_el_mismo_lugar(self):
        lugar = self.crear_lugar(901)
        uid = self.crear_conductor()
        db.reservar_lugar(lugar["id"], uid)
        ok, _ = db.reservar_lugar(lugar["id"], uid)
        self.assertFalse(ok)
        self.assertEqual(len(self.reservas_de(uid)), 1)
 
    def test_reservar_lugar_inexistente_falla_sin_excepcion(self):
        uid = self.crear_conductor()
        ok, _ = db.reservar_lugar(999999, uid)
        self.assertFalse(ok)
 
    def test_cancelar_libera_el_lugar_y_marca_la_reserva_cancelada(self):
        lugar = self.crear_lugar(901)
        uid = self.crear_conductor()
        db.reservar_lugar(lugar["id"], uid)
        reserva_id = self.reservas_de(uid)[0]["id"]
 
        ok, msg = db.cancelar_reserva(reserva_id)
 
        self.assertTrue(ok, msg)
        self.assertTrue(self.lugar_por_id(lugar["id"])["disponible"])
        self.assertEqual(self.reservas_de(uid)[0]["estado"], "cancelada")
 
    def test_no_se_puede_cancelar_dos_veces(self):
        lugar = self.crear_lugar(901)
        uid = self.crear_conductor()
        db.reservar_lugar(lugar["id"], uid)
        reserva_id = self.reservas_de(uid)[0]["id"]
 
        self.assertTrue(db.cancelar_reserva(reserva_id)[0])
        self.assertFalse(db.cancelar_reserva(reserva_id)[0])
 
    def test_cancelar_reserva_inexistente_falla_sin_excepcion(self):
        ok, _ = db.cancelar_reserva(999999)
        self.assertFalse(ok)
 
    def test_cancelar_una_reserva_no_libera_un_lugar_reservado_por_otro(self):
        """Ciclo: A reserva, A cancela, B reserva. Si A vuelve a cancelar, B no debe perder el lugar."""
        lugar = self.crear_lugar(901)
        a = self.crear_conductor("ana", "clave1", "Ana")
        b = self.crear_conductor("beto", "clave2", "Beto")
 
        db.reservar_lugar(lugar["id"], a)
        reserva_a = self.reservas_de(a)[0]["id"]
        db.cancelar_reserva(reserva_a)
        self.assertTrue(db.reservar_lugar(lugar["id"], b)[0])
 
        db.cancelar_reserva(reserva_a)  # cancelación repetida de la reserva vieja de A
        self.assertFalse(self.lugar_por_id(lugar["id"])["disponible"], "El lugar de Beto fue liberado por error")
 
    def test_se_puede_volver_a_reservar_luego_de_cancelar(self):
        lugar = self.crear_lugar(901)
        uid = self.crear_conductor()
        db.reservar_lugar(lugar["id"], uid)
        db.cancelar_reserva(self.reservas_de(uid)[0]["id"])
        self.assertTrue(db.reservar_lugar(lugar["id"], uid)[0])
 
    def test_cada_usuario_ve_solo_sus_reservas(self):
        l1, l2 = self.crear_lugar(901), self.crear_lugar(902)
        a = self.crear_conductor("ana", "clave1", "Ana")
        b = self.crear_conductor("beto", "clave2", "Beto")
        db.reservar_lugar(l1["id"], a)
        db.reservar_lugar(l2["id"], b)
 
        self.assertEqual([r["numero"] for r in self.reservas_de(a)], [901])
        self.assertEqual([r["numero"] for r in self.reservas_de(b)], [902])
 
 
# --------------------------------------------------------------------------- #
# VALIDACIONES ESPERADAS (si fallan, falta validar en database.py o en la UI)
# --------------------------------------------------------------------------- #
class TestValidacionesEsperadas(BaseTest):
    def test_precios_invalidos_son_rechazados(self):
        est = self.est_id()
        for i, precio in enumerate([-50.0, 0, -0.01]):
            with self.subTest(precio=precio):
                ok, _ = db.agregar_lugar(910 + i, "auto", precio, est)
                self.assertFalse(ok, f"agregar_lugar aceptó el precio {precio}")
 
    def test_numeros_de_lugar_invalidos_son_rechazados(self):
        est = self.est_id()
        for numero in (0, -5):
            with self.subTest(numero=numero):
                ok, _ = db.agregar_lugar(numero, "auto", 100.0, est)
                self.assertFalse(ok, f"agregar_lugar aceptó el número {numero}")
 
    def test_tipo_de_vehiculo_invalido_es_rechazado(self):
        ok, _ = db.agregar_lugar(920, "bicicleta", 100.0, self.est_id())
        self.assertFalse(ok, "agregar_lugar aceptó un tipo de vehículo que no existe")
 
    def test_numero_de_lugar_duplicado_en_el_mismo_estacionamiento_es_rechazado(self):
        est = self.est_id()
        self.crear_lugar(901, est=est)
        ok, _ = db.agregar_lugar(901, "moto", 50.0, est)
        self.assertFalse(ok, "Se pudo crear dos veces el lugar #901 en el mismo estacionamiento")
 
    def test_modificar_lugar_a_un_numero_ya_usado_es_rechazado(self):
        a = self.crear_lugar(901)
        self.crear_lugar(902)
        ok, _ = db.modificar_lugar(a["id"], 902, "auto", 100.0, True)
        self.assertFalse(ok, "modificar_lugar permitió duplicar el número 902")
 
    def test_registro_con_usuario_vacio_es_rechazado(self):
        # La UI chequea "vacío" ANTES de hacer strip(): el texto "   " pasa el chequeo y llega como "".
        ok, _ = db.crear_usuario("", "clave123", "Juan", "conductor")
        self.assertFalse(ok)
 
    def test_registro_con_password_vacia_es_rechazado(self):
        ok, _ = db.crear_usuario("juan", "", "Juan", "conductor")
        self.assertFalse(ok)
 
    def test_registro_con_rol_inexistente_es_rechazado(self):
        ok, _ = db.crear_usuario("juan", "clave123", "Juan", "superadmin")
        self.assertFalse(ok)
 
    def test_reservar_con_usuario_inexistente_es_rechazado(self):
        lugar = self.crear_lugar(901)
        ok, _ = db.reservar_lugar(lugar["id"], 999999)
        self.assertFalse(ok)
        self.assertTrue(self.lugar_por_id(lugar["id"])["disponible"], "El lugar quedó ocupado por un usuario inexistente")
 
 
if __name__ == "__main__":
    unittest.main(verbosity=2)