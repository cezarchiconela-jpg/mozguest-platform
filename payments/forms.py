from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'payment_method',
            'amount',
            'transaction_reference',
            'proof',
        ]

        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'step': '0.01'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'placeholder': 'Ex: ID da transacção M-Pesa/e-Mola'
            }),
            'proof': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
        }
