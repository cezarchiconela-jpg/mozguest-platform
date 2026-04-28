from django import forms
from .models import Property, Room, PropertyPhoto


MAX_IMAGE_SIZE_MB = 5


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget",
            MultipleFileInput(attrs={
                "multiple": True,
                "accept": "image/*",
                "class": "w-full px-4 py-3 rounded-xl border border-slate-300"
            })
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        cleaned_files = []

        for file_obj in files:
            cleaned = forms.FileField.clean(self, file_obj, initial)

            if cleaned:
                if cleaned.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                    raise forms.ValidationError(
                        f'Cada imagem deve ter no máximo {MAX_IMAGE_SIZE_MB}MB.'
                    )

                if not cleaned.content_type.startswith('image/'):
                    raise forms.ValidationError('Apenas ficheiros de imagem são permitidos.')

                cleaned_files.append(cleaned)

        return cleaned_files


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name',
            'property_type',
            'description',
            'province',
            'city',
            'district',
            'neighbourhood',
            'address_reference',
            'latitude',
            'longitude',
            'phone',
            'whatsapp',
            'email',
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'property_type': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'rows': 5}),
            'province': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'district': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'neighbourhood': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'address_reference': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.0000001'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
        }


class RoomForm(forms.ModelForm):
    photos = MultipleFileField(
        label='Fotografias do quarto/unidade',
        required=False,
        help_text='Pode seleccionar várias imagens ao mesmo tempo.'
    )

    class Meta:
        model = Room
        fields = [
            'property',
            'name',
            'room_type',
            'description',
            'capacity',
            'price_hour',
            'price_day',
            'price_night',
            'price_month',
            'minimum_hours',
            'has_private_bathroom',
            'has_ac',
            'has_wifi',
            'has_parking',
            'is_available',
        ]

        widgets = {
            'property': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'room_type': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'rows': 4}),
            'capacity': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'min': 1}),
            'price_hour': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.01'}),
            'price_day': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.01'}),
            'price_night': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.01'}),
            'price_month': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'step': '0.01'}),
            'minimum_hours': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'min': 1}),
            'has_private_bathroom': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'has_ac': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
        }


class PropertyPhotoForm(forms.ModelForm):
    class Meta:
        model = PropertyPhoto
        fields = [
            'property',
            'room',
            'image',
            'caption',
            'is_main',
        ]

        widgets = {
            'property': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'room': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'image': forms.FileInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'h-5 w-5'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image:
            if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(f'A imagem deve ter no máximo {MAX_IMAGE_SIZE_MB}MB.')

            if not image.content_type.startswith('image/'):
                raise forms.ValidationError('Apenas ficheiros de imagem são permitidos.')

        return image
