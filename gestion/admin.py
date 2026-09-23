from django.contrib import admin

from .models import Cliente, Cuenta, Transaccion


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'rut', 'telefono', 'fecha_alta')
    search_fields = ('nombre', 'email', 'rut')
    list_filter = ('fecha_alta',)


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('numero_cuenta', 'cliente', 'tipo', 'saldo', 'activa')
    list_filter = ('tipo', 'activa')
    search_fields = ('numero_cuenta', 'cliente__nombre')
    autocomplete_fields = ('cliente',)


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'cuenta_origen', 'monto', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('cuenta_origen__numero_cuenta', 'descripcion')
    filter_horizontal = ('cuentas_relacionadas',)
