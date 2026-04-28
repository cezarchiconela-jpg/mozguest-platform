from django import forms
from .models import SupportTicket
from bookings.models import Booking


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = [
            'booking',
            'category',
            'subject',
            'description',
            'priority',
        ]

        widgets = {
            'booking': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'placeholder': 'Resumo do problema'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'rows': 5,
                'placeholder': 'Explique com detalhes o que aconteceu'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        if hasattr(self.user, 'owner_profile'):
            self.fields['booking'].queryset = Booking.objects.filter(property__owner=self.user)
        else:
            self.fields['booking'].queryset = Booking.objects.filter(client=self.user)

        self.fields['booking'].required = False


class AdminSupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = [
            'status',
            'priority',
            'admin_response',
        ]

        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'admin_response': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'rows': 5,
                'placeholder': 'Resposta ou decisão da administração'
            }),
        }
