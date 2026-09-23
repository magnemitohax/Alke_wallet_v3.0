from django import forms

from .models import Cliente, Cuenta, Transaccion


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'email', 'telefono', 'rut']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['cliente', 'numero_cuenta', 'tipo', 'saldo', 'activa']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'saldo': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['cuenta_origen', 'cuentas_relacionadas', 'tipo', 'monto', 'descripcion']
        widgets = {
            'cuenta_origen': forms.Select(attrs={'class': 'form-control'}),
            'cuentas_relacionadas': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AjusteSaldoForm(forms.Form):
    OPERACION_CHOICES = [
        ('DEPOSITO', 'Agregar saldo (depósito)'),
        ('EXTRACCION', 'Descontar saldo (extracción)'),
    ]

    operacion = forms.ChoiceField(
        choices=OPERACION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    monto = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    descripcion = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class TransferenciaForm(forms.Form):
    cuenta_destino = forms.ModelChoiceField(
        queryset=Cuenta.objects.none(),
        label='Cuenta destino',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    monto = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    descripcion = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, cuenta_origen=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Cuenta.objects.filter(activa=True)
        if cuenta_origen is not None:
            queryset = queryset.exclude(pk=cuenta_origen.pk)
        self.fields['cuenta_destino'].queryset = queryset
