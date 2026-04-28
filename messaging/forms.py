from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']

        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'rows': 3,
                'placeholder': 'Escreva a sua mensagem...'
            }),
        }
