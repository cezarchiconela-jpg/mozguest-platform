from django import forms
from .models import Payment


MAX_PROOF_SIZE_MB = 5


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
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300 bg-slate-100 text-slate-600',
                'step': '0.01',
                'readonly': 'readonly'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'placeholder': 'Ex: ID da transacção M-Pesa/e-Mola'
            }),
            'proof': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, fixed_amount=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fixed_amount = fixed_amount
        self.fields['amount'].disabled = True
        if fixed_amount is not None:
            self.fields['amount'].initial = fixed_amount

    def clean_amount(self):
        if self.fixed_amount is not None:
            return self.fixed_amount
        if self.instance and self.instance.pk:
            return self.instance.amount
        return self.cleaned_data.get('amount')

    def clean_proof(self):
        proof = self.cleaned_data.get('proof')
        if proof:
            if proof.size > MAX_PROOF_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(f'O comprovativo deve ter no máximo {MAX_PROOF_SIZE_MB}MB.')

            content_type = getattr(proof, 'content_type', '')
            if not content_type.startswith('image/'):
                raise forms.ValidationError('Envie uma imagem válida como comprovativo.')

        return proof
