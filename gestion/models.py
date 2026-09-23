from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Cliente(models.Model):
    """Cliente de Alke Financial. Relación Uno a Uno con User (login opcional)."""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cliente',
        help_text='Usuario del sistema (login) asociado a este cliente, si tiene acceso web.'
    )
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    rut = models.CharField(max_length=12, unique=True, help_text='Formato: 12345678-9')
    fecha_alta = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Cuenta(models.Model):
    """Cuenta digital de un cliente. Relación Muchos a Uno con Cliente."""
    TIPO_CHOICES = [
        ('AHORRO', 'Caja de ahorro'),
        ('CORRIENTE', 'Cuenta corriente'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='cuentas'
    )
    numero_cuenta = models.CharField(max_length=20, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='AHORRO')
    saldo = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)]
    )
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.numero_cuenta} ({self.get_tipo_display()}) - {self.cliente.nombre}'


class Transaccion(models.Model):
    """Movimiento sobre una cuenta. Relación Muchos a Muchos con Cuenta
    (cuentas_relacionadas) para operaciones que involucran más de una cuenta."""
    TIPO_CHOICES = [
        ('DEPOSITO', 'Depósito'),
        ('EXTRACCION', 'Extracción'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    cuenta_origen = models.ForeignKey(
        Cuenta,
        on_delete=models.CASCADE,
        related_name='transacciones'
    )
    cuentas_relacionadas = models.ManyToManyField(
        Cuenta,
        blank=True,
        related_name='transacciones_relacionadas',
        help_text='Otras cuentas involucradas (p. ej. cuenta destino en una transferencia).'
    )
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    monto = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    descripcion = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} de ${self.monto} - {self.cuenta_origen.numero_cuenta}'
