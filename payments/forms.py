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

        if not getattr(self.instance, 'proof', None):
            self.fields['proof'].required = True

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


class GatewayPaymentForm(forms.Form):
    phone_number = forms.CharField(
        label='Número de telefone',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Ex: 84xxxxxxx / 85xxxxxxx / 86xxxxxxx / 87xxxxxxx'
        })
    )

    def clean_phone_number(self):
        value = (self.cleaned_data.get('phone_number') or '').strip().replace(' ', '')
        value = value.replace('-', '').replace('(', '').replace(')', '')

        if value.startswith('+'):
            digits = '+' + ''.join(ch for ch in value[1:] if ch.isdigit())
        else:
            digits = ''.join(ch for ch in value if ch.isdigit())

        normalized = digits
        if normalized.startswith('00258'):
            normalized = '+' + normalized[2:]
        elif normalized.startswith('258') and len(normalized) >= 12:
            normalized = '+' + normalized
        elif normalized.startswith('8') and len(normalized) == 9:
            normalized = '+258' + normalized

        if not normalized.startswith('+258') or len(normalized) != 13:
            raise forms.ValidationError('Informe um número moçambicano válido. Exemplo: 84xxxxxxx ou +25884xxxxxxx.')

        return normalized


class OwnerPayoutActionForm(forms.Form):
    method = forms.ChoiceField(
        label='Método de liquidação',
        choices=[('', 'Seleccione o método')] + [
            ('mpesa', 'M-Pesa'),
            ('emola', 'e-Mola'),
            ('bank_transfer', 'Transferência bancária'),
            ('cash', 'Numerário'),
            ('other', 'Outro'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
        })
    )

    payout_reference = forms.CharField(
        label='Referência da liquidação',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Ex: ID M-Pesa/e-Mola, referência bancária ou nota interna'
        })
    )

    admin_notes = forms.CharField(
        label='Notas administrativas',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'rows': 3,
            'placeholder': 'Observações internas, motivo de retenção ou detalhes da liquidação.'
        })
    )


class RefundReviewForm(forms.Form):
    refund_status = forms.ChoiceField(
        label='Decisão sobre reembolso',
        choices=[
            ('no_refund', 'Sem reembolso'),
            ('partial_refund', 'Reembolso parcial'),
            ('full_refund', 'Reembolso total'),
            ('refunded', 'Reembolsado'),
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'})
    )
    refund_amount = forms.DecimalField(
        label='Valor de reembolso',
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.01'})
    )
    refund_reference = forms.CharField(
        label='Referência do reembolso',
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'})
    )
    refund_notes = forms.CharField(
        label='Notas da decisão',
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'rows': 3})
    )
