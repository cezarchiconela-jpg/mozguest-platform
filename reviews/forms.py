from django import forms
from .models import Review


RATING_CHOICES = [
    (1, '1 - Muito fraco'),
    (2, '2 - Fraco'),
    (3, '3 - Razoável'),
    (4, '4 - Bom'),
    (5, '5 - Excelente'),
]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            'customer_name',
            'rating',
            'cleanliness_rating',
            'security_rating',
            'location_rating',
            'comfort_rating',
            'service_rating',
            'value_rating',
            'comment',
        ]

        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'placeholder': 'O seu nome'
            }),
            'rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'cleanliness_rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'security_rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'location_rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'comfort_rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'service_rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'value_rating': forms.Select(choices=RATING_CHOICES, attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
                'rows': 5,
                'placeholder': 'Partilhe a sua experiência neste alojamento'
            }),
        }
