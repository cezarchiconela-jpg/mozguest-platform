from django import forms
from django.utils import timezone
from .models import Booking, AvailabilityBlock


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'booking_type',
            'checkin_date',
            'checkin_time',
            'checkout_date',
            'checkout_time',
            'number_of_guests',
            'client_notes',
        ]

        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'placeholder': 'Nome completo'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'placeholder': 'Telefone / WhatsApp'}),
            'customer_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'placeholder': 'email@exemplo.com'}),
            'booking_type': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'checkin_date': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'type': 'date'}),
            'checkin_time': forms.TimeInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'type': 'time'}),
            'checkout_date': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'type': 'date'}),
            'checkout_time': forms.TimeInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'type': 'time'}),
            'number_of_guests': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'min': '1'}),
            'client_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'rows': 4, 'placeholder': 'Observações adicionais'}),
        }

    def clean_checkin_date(self):
        checkin_date = self.cleaned_data.get('checkin_date')
        today = timezone.localdate()
        if checkin_date and checkin_date < today:
            raise forms.ValidationError('A data de entrada não pode ser anterior à data actual.')
        return checkin_date

    def clean(self):
        cleaned_data = super().clean()
        booking_type = cleaned_data.get('booking_type')
        checkin_date = cleaned_data.get('checkin_date')
        checkin_time = cleaned_data.get('checkin_time')
        checkout_date = cleaned_data.get('checkout_date')
        checkout_time = cleaned_data.get('checkout_time')
        number_of_guests = cleaned_data.get('number_of_guests')

        if number_of_guests and number_of_guests < 1:
            raise forms.ValidationError('O número de pessoas deve ser no mínimo 1.')

        if booking_type == 'hour':
            if not checkin_time:
                raise forms.ValidationError('Para reserva por hora, informe a hora de entrada.')
            if not checkout_time:
                raise forms.ValidationError('Para reserva por hora, informe a hora de saída.')
            if not checkout_date:
                checkout_date = checkin_date
                cleaned_data['checkout_date'] = checkout_date

        if booking_type in ['day', 'night', 'month']:
            if not checkout_date:
                raise forms.ValidationError('Informe a data de saída.')

        if checkin_date and checkout_date:
            if checkout_date < checkin_date:
                raise forms.ValidationError('A data de saída não pode ser anterior à data de entrada.')
            if checkout_date == checkin_date and checkin_time and checkout_time and checkout_time <= checkin_time:
                raise forms.ValidationError('A hora de saída deve ser posterior à hora de entrada.')

        return cleaned_data


class AvailabilityBlockForm(forms.ModelForm):
    class Meta:
        model = AvailabilityBlock
        fields = ['room', 'start_datetime', 'end_datetime', 'reason', 'notes']
        widgets = {
            'room': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'type': 'datetime-local'}),
            'reason': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'rows': 4, 'placeholder': 'Observações sobre o bloqueio'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise forms.ValidationError('A data/hora final deve ser posterior à data/hora inicial.')
        return cleaned_data
