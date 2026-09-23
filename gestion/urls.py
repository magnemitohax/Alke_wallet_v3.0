from django.urls import path

from . import views

urlpatterns = [
    # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='cliente_delete'),

    # Cuentas
    path('cuentas/', views.CuentaListView.as_view(), name='cuenta_list'),
    path('cuentas/nueva/', views.CuentaCreateView.as_view(), name='cuenta_create'),
    path('cuentas/<int:pk>/', views.CuentaDetailView.as_view(), name='cuenta_detail'),
    path('cuentas/<int:pk>/editar/', views.CuentaUpdateView.as_view(), name='cuenta_update'),
    path('cuentas/<int:pk>/eliminar/', views.CuentaDeleteView.as_view(), name='cuenta_delete'),
    path('cuentas/<int:pk>/saldo/', views.cuenta_ajustar_saldo, name='cuenta_ajustar_saldo'),
    path('cuentas/<int:pk>/transferir/', views.cuenta_transferir, name='cuenta_transferir'),

    # Transacciones
    path('transacciones/', views.TransaccionListView.as_view(), name='transaccion_list'),
    path('transacciones/nueva/', views.TransaccionCreateView.as_view(), name='transaccion_create'),
    path('transacciones/<int:pk>/', views.TransaccionDetailView.as_view(), name='transaccion_detail'),
    path('transacciones/<int:pk>/editar/', views.TransaccionUpdateView.as_view(), name='transaccion_update'),
    path('transacciones/<int:pk>/eliminar/', views.TransaccionDeleteView.as_view(), name='transaccion_delete'),

    # Reportes
    path('reportes/', views.ReporteView.as_view(), name='reportes'),
]
