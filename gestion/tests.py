from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cliente, Cuenta, Transaccion


class ModeloClienteTest(TestCase):
    def test_str_devuelve_nombre(self):
        cliente = Cliente.objects.create(nombre="Ana García", email="ana@test.com", rut="1")
        self.assertEqual(str(cliente), "Ana García")


class ModeloCuentaTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nombre="Luis Pérez", email="luis@test.com", rut="2")

    def test_relacion_muchos_a_uno(self):
        Cuenta.objects.create(cliente=self.cliente, numero_cuenta="AW-100", saldo=1000)
        Cuenta.objects.create(cliente=self.cliente, numero_cuenta="AW-101", saldo=500)
        self.assertEqual(self.cliente.cuentas.count(), 2)

    def test_saldo_no_admite_negativos(self):
        cuenta = Cuenta(cliente=self.cliente, numero_cuenta="AW-102", saldo=-10)
        with self.assertRaises(Exception):
            cuenta.full_clean()


class ModeloTransaccionTest(TestCase):
    def setUp(self):
        cliente = Cliente.objects.create(nombre="Marta Ruiz", email="marta@test.com", rut="3")
        self.cuenta_origen = Cuenta.objects.create(cliente=cliente, numero_cuenta="AW-200", saldo=2000)
        self.cuenta_destino = Cuenta.objects.create(cliente=cliente, numero_cuenta="AW-201", saldo=0)

    def test_relacion_muchos_a_muchos(self):
        t = Transaccion.objects.create(
            cuenta_origen=self.cuenta_origen, tipo="TRANSFERENCIA", monto=300
        )
        t.cuentas_relacionadas.add(self.cuenta_destino)
        self.assertIn(self.cuenta_destino, t.cuentas_relacionadas.all())
        self.assertIn(t, self.cuenta_destino.transacciones_relacionadas.all())


class VistasCRUDTest(TestCase):
    """Prueba de integración: las vistas CRUD requieren login (LoginRequiredMixin)
    y, una vez autenticado, permiten crear y listar registros."""

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="clave12345")
        self.cliente = Cliente.objects.create(nombre="Cliente Test", email="test@test.com", rut="9")

    def test_lista_clientes_redirige_si_no_hay_login(self):
        response = self.client.get(reverse('cliente_list'))
        self.assertEqual(response.status_code, 302)

    def test_lista_clientes_autenticado(self):
        self.client.login(username="tester", password="clave12345")
        response = self.client.get(reverse('cliente_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente Test")

    def test_crear_cliente_via_post(self):
        self.client.login(username="tester", password="clave12345")
        response = self.client.post(reverse('cliente_create'), {
            'nombre': 'Nuevo Cliente',
            'email': 'nuevo@test.com',
            'telefono': '',
            'rut': '111',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cliente.objects.filter(email='nuevo@test.com').exists())


class AjustarSaldoTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester2", password="clave12345")
        self.client.login(username="tester2", password="clave12345")
        cliente = Cliente.objects.create(nombre="Sofía Muñoz", email="sofia@test.com", rut="4")
        self.cuenta = Cuenta.objects.create(cliente=cliente, numero_cuenta="AW-300", saldo=1000)

    def test_deposito_aumenta_saldo_y_crea_transaccion(self):
        response = self.client.post(reverse('cuenta_ajustar_saldo', args=[self.cuenta.pk]), {
            'operacion': 'DEPOSITO',
            'monto': '500',
            'descripcion': 'Depósito de prueba',
        })
        self.assertEqual(response.status_code, 302)
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, 1500)
        self.assertTrue(
            Transaccion.objects.filter(cuenta_origen=self.cuenta, tipo='DEPOSITO', monto=500).exists()
        )

    def test_extraccion_descuenta_saldo(self):
        response = self.client.post(reverse('cuenta_ajustar_saldo', args=[self.cuenta.pk]), {
            'operacion': 'EXTRACCION',
            'monto': '300',
            'descripcion': '',
        })
        self.assertEqual(response.status_code, 302)
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, 700)

    def test_extraccion_rechaza_monto_mayor_al_saldo(self):
        response = self.client.post(reverse('cuenta_ajustar_saldo', args=[self.cuenta.pk]), {
            'operacion': 'EXTRACCION',
            'monto': '5000',
            'descripcion': '',
        })
        self.assertEqual(response.status_code, 200)  # vuelve a mostrar el formulario con error
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.saldo, 1000)  # saldo sin cambios


class TransferenciaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester3", password="clave12345")
        self.client.login(username="tester3", password="clave12345")
        cliente = Cliente.objects.create(nombre="Pedro Silva", email="pedro@test.com", rut="5")
        self.cuenta_origen = Cuenta.objects.create(cliente=cliente, numero_cuenta="AW-400", saldo=1000)
        self.cuenta_destino = Cuenta.objects.create(cliente=cliente, numero_cuenta="AW-401", saldo=200)

    def test_transferencia_mueve_saldo_entre_cuentas(self):
        response = self.client.post(reverse('cuenta_transferir', args=[self.cuenta_origen.pk]), {
            'cuenta_destino': self.cuenta_destino.pk,
            'monto': '400',
            'descripcion': 'Transferencia de prueba',
        })
        self.assertEqual(response.status_code, 302)
        self.cuenta_origen.refresh_from_db()
        self.cuenta_destino.refresh_from_db()
        self.assertEqual(self.cuenta_origen.saldo, 600)
        self.assertEqual(self.cuenta_destino.saldo, 600)
        transaccion = Transaccion.objects.get(cuenta_origen=self.cuenta_origen, tipo='TRANSFERENCIA')
        self.assertIn(self.cuenta_destino, transaccion.cuentas_relacionadas.all())

    def test_transferencia_rechaza_monto_mayor_al_saldo(self):
        response = self.client.post(reverse('cuenta_transferir', args=[self.cuenta_origen.pk]), {
            'cuenta_destino': self.cuenta_destino.pk,
            'monto': '5000',
            'descripcion': '',
        })
        self.assertEqual(response.status_code, 200)
        self.cuenta_origen.refresh_from_db()
        self.cuenta_destino.refresh_from_db()
        self.assertEqual(self.cuenta_origen.saldo, 1000)
        self.assertEqual(self.cuenta_destino.saldo, 200)

    def test_transferencia_no_permite_misma_cuenta_como_destino(self):
        response = self.client.post(reverse('cuenta_transferir', args=[self.cuenta_origen.pk]), {
            'cuenta_destino': self.cuenta_origen.pk,
            'monto': '100',
            'descripcion': '',
        })
        self.assertEqual(response.status_code, 200)  # formulario inválido: no aparece como opción
        self.cuenta_origen.refresh_from_db()
        self.assertEqual(self.cuenta_origen.saldo, 1000)


class CuentaListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester4", password="clave12345")
        self.client.login(username="tester4", password="clave12345")
        cliente = Cliente.objects.create(nombre="Valentina Rojas", email="valentina@test.com", rut="6")
        self.ahorro = Cuenta.objects.create(
            cliente=cliente, numero_cuenta="AW-500", tipo="AHORRO", saldo=1000
        )
        self.corriente = Cuenta.objects.create(
            cliente=cliente, numero_cuenta="AW-501", tipo="CORRIENTE", saldo=2000
        )
        self.inactiva = Cuenta.objects.create(
            cliente=cliente, numero_cuenta="AW-502", tipo="AHORRO", saldo=500, activa=False
        )

    def test_filter_por_tipo_devuelve_solo_ese_tipo(self):
        response = self.client.get(reverse('cuenta_list') + '?tipo=AHORRO')
        self.assertEqual(response.status_code, 200)
        cuentas = list(response.context['cuentas'])
        self.assertIn(self.ahorro, cuentas)
        self.assertNotIn(self.corriente, cuentas)

    def test_exclude_deja_fuera_las_cuentas_inactivas(self):
        response = self.client.get(reverse('cuenta_list'))
        cuentas = list(response.context['cuentas'])
        self.assertNotIn(self.inactiva, cuentas)
        self.assertIn(self.ahorro, cuentas)
        self.assertIn(self.corriente, cuentas)
