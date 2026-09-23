from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection, transaction
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
)

from .forms import AjusteSaldoForm, ClienteForm, CuentaForm, TransaccionForm, TransferenciaForm
from .models import Cliente, Cuenta, Transaccion


# ---------- CLIENTE (CRUD) ----------

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'gestion/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10


class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'gestion/cliente_detail.html'
    context_object_name = 'cliente'


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'gestion/cliente_form.html'
    success_url = reverse_lazy('cliente_list')


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'gestion/cliente_form.html'
    success_url = reverse_lazy('cliente_list')


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'gestion/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')


# ---------- CUENTA (CRUD) ----------

class CuentaListView(LoginRequiredMixin, ListView):
    model = Cuenta
    template_name = 'gestion/cuenta_list.html'
    context_object_name = 'cuentas'
    paginate_by = 10

    def get_queryset(self):
        # Filtro por tipo (?tipo=AHORRO) y exclusión de cuentas inactivas
        queryset = super().get_queryset().select_related('cliente')
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset.exclude(activa=False)


class CuentaDetailView(LoginRequiredMixin, DetailView):
    model = Cuenta
    template_name = 'gestion/cuenta_detail.html'
    context_object_name = 'cuenta'


class CuentaCreateView(LoginRequiredMixin, CreateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = 'gestion/cuenta_form.html'
    success_url = reverse_lazy('cuenta_list')


class CuentaUpdateView(LoginRequiredMixin, UpdateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = 'gestion/cuenta_form.html'
    success_url = reverse_lazy('cuenta_list')


class CuentaDeleteView(LoginRequiredMixin, DeleteView):
    model = Cuenta
    template_name = 'gestion/cuenta_confirm_delete.html'
    success_url = reverse_lazy('cuenta_list')


@login_required
def cuenta_ajustar_saldo(request, pk):
    """Agrega o descuenta saldo de una cuenta y registra la transacción."""
    cuenta = get_object_or_404(Cuenta, pk=pk)

    if request.method == 'POST':
        form = AjusteSaldoForm(request.POST)
        if form.is_valid():
            operacion = form.cleaned_data['operacion']
            monto = form.cleaned_data['monto']
            descripcion = form.cleaned_data['descripcion']

            if operacion == 'EXTRACCION' and monto > cuenta.saldo:
                form.add_error('monto', 'El monto supera el saldo disponible.')
            else:
                with transaction.atomic():
                    if operacion == 'DEPOSITO':
                        cuenta.saldo = cuenta.saldo + monto
                    else:
                        cuenta.saldo = cuenta.saldo - monto
                    cuenta.save()

                    Transaccion.objects.create(
                        cuenta_origen=cuenta,
                        tipo=operacion,
                        monto=monto,
                        descripcion=descripcion,
                    )
                messages.success(request, 'Saldo actualizado correctamente.')
                return redirect('cuenta_detail', pk=cuenta.pk)
    else:
        form = AjusteSaldoForm()

    return render(request, 'gestion/cuenta_ajustar_saldo.html', {
        'cuenta': cuenta,
        'form': form,
    })


@login_required
def cuenta_transferir(request, pk):
    """Transfiere saldo de una cuenta a otra y registra la transacción."""
    cuenta_origen = get_object_or_404(Cuenta, pk=pk)

    if request.method == 'POST':
        form = TransferenciaForm(request.POST, cuenta_origen=cuenta_origen)
        if form.is_valid():
            cuenta_destino = form.cleaned_data['cuenta_destino']
            monto = form.cleaned_data['monto']
            descripcion = form.cleaned_data['descripcion']

            if monto > cuenta_origen.saldo:
                form.add_error('monto', 'El monto supera el saldo disponible.')
            else:
                with transaction.atomic():
                    cuenta_origen.saldo = cuenta_origen.saldo - monto
                    cuenta_origen.save()

                    cuenta_destino.saldo = cuenta_destino.saldo + monto
                    cuenta_destino.save()

                    transaccion_creada = Transaccion.objects.create(
                        cuenta_origen=cuenta_origen,
                        tipo='TRANSFERENCIA',
                        monto=monto,
                        descripcion=descripcion,
                    )
                    transaccion_creada.cuentas_relacionadas.add(cuenta_destino)
                messages.success(request, 'Transferencia realizada correctamente.')
                return redirect('cuenta_detail', pk=cuenta_origen.pk)
    else:
        form = TransferenciaForm(cuenta_origen=cuenta_origen)

    return render(request, 'gestion/cuenta_transferir.html', {
        'cuenta': cuenta_origen,
        'form': form,
    })


# ---------- TRANSACCION (CRUD) ----------

class TransaccionListView(LoginRequiredMixin, ListView):
    model = Transaccion
    template_name = 'gestion/transaccion_list.html'
    context_object_name = 'transacciones'
    paginate_by = 10

    def get_queryset(self):
        return super().get_queryset().select_related('cuenta_origen')


class TransaccionDetailView(LoginRequiredMixin, DetailView):
    model = Transaccion
    template_name = 'gestion/transaccion_detail.html'
    context_object_name = 'transaccion'


class TransaccionCreateView(LoginRequiredMixin, CreateView):
    model = Transaccion
    form_class = TransaccionForm
    template_name = 'gestion/transaccion_form.html'
    success_url = reverse_lazy('transaccion_list')


class TransaccionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaccion
    form_class = TransaccionForm
    template_name = 'gestion/transaccion_form.html'
    success_url = reverse_lazy('transaccion_list')


class TransaccionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaccion
    template_name = 'gestion/transaccion_confirm_delete.html'
    success_url = reverse_lazy('transaccion_list')


# ---------- REPORTES: consultas avanzadas (annotate + raw SQL) ----------

class ReporteView(LoginRequiredMixin, TemplateView):
    """Reportes con filter()/exclude(), annotate() y SQL vía cursor."""
    template_name = 'gestion/reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Clientes con cuentas activas: annotate() + filter()/exclude()
        clientes_con_cuentas = (
            Cliente.objects
            .annotate(total_cuentas=Count('cuentas'),
                      saldo_total=Sum('cuentas__saldo'))
            .filter(total_cuentas__gt=0)
            .exclude(cuentas__activa=False)
            .distinct()
        )

        # Top 5 cuentas por saldo
        cuentas_top = Cuenta.objects.filter(activa=True).order_by('-saldo')[:5]

        # Resumen por tipo de transacción, con SQL vía cursor
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tipo, COUNT(*) AS cantidad, COALESCE(SUM(monto), 0) AS total
                FROM gestion_transaccion
                GROUP BY tipo
                ORDER BY total DESC
                """
            )
            columnas = [col[0] for col in cursor.description]
            resumen_transacciones = [
                dict(zip(columnas, fila)) for fila in cursor.fetchall()
            ]

        context['clientes_con_cuentas'] = clientes_con_cuentas
        context['cuentas_top'] = cuentas_top
        context['resumen_transacciones'] = resumen_transacciones
        return context
