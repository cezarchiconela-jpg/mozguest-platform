from django import forms
from .models import Property, Room, PropertyPhoto


MAX_IMAGE_SIZE_MB = 5

FIELD_CLS = 'w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            MultipleFileInput(attrs={
                'multiple': True,
                'accept': 'image/*',
                'class': FIELD_CLS,
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

                if not getattr(cleaned, 'content_type', '').startswith('image/'):
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
            'name': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: +258 Guest Residencial Polana'}),
            'property_type': forms.Select(attrs={'class': FIELD_CLS}),
            'description': forms.Textarea(attrs={
                'class': FIELD_CLS,
                'rows': 6,
                'placeholder': 'Descreva o alojamento, o ambiente, segurança, comodidades, tipo de clientes indicado, regras principais e pontos de referência.',
            }),
            'province': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Maputo Cidade'}),
            'city': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Maputo'}),
            'district': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: KaMpfumo'}),
            'neighbourhood': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Polana'}),
            'address_reference': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Próximo da avenida principal, perto de...'}),
            'latitude': forms.NumberInput(attrs={'class': FIELD_CLS, 'step': '0.0000001', 'placeholder': '-25.9653000'}),
            'longitude': forms.NumberInput(attrs={'class': FIELD_CLS, 'step': '0.0000001', 'placeholder': '32.5892000'}),
            'phone': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: 840000000'}),
            'whatsapp': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: 258840000000'}),
            'email': forms.EmailInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: reservas@alojamento.co.mz'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        phone = (cleaned_data.get('phone') or '').strip()
        whatsapp = (cleaned_data.get('whatsapp') or '').strip()
        email = (cleaned_data.get('email') or '').strip()
        description = (cleaned_data.get('description') or '').strip()

        if not any([phone, whatsapp, email]):
            raise forms.ValidationError('Informe pelo menos um contacto do alojamento: telefone, WhatsApp ou e-mail.')

        if description and len(description) < 60:
            self.add_error('description', 'A descrição está muito curta. Escreva pelo menos 60 caracteres para ajudar o cliente a confiar no alojamento.')

        return cleaned_data


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
            'property': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Suíte Executiva 01'}),
            'room_type': forms.Select(attrs={'class': FIELD_CLS}),
            'description': forms.Textarea(attrs={'class': FIELD_CLS, 'rows': 4, 'placeholder': 'Descreva cama, casa de banho, conforto, vista, privacidade e regras desta unidade.'}),
            'capacity': forms.NumberInput(attrs={'class': FIELD_CLS, 'min': 1}),
            'price_hour': forms.NumberInput(attrs={'class': FIELD_CLS, 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 750'}),
            'price_day': forms.NumberInput(attrs={'class': FIELD_CLS, 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 3500'}),
            'price_night': forms.NumberInput(attrs={'class': FIELD_CLS, 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 2500'}),
            'price_month': forms.NumberInput(attrs={'class': FIELD_CLS, 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 45000'}),
            'minimum_hours': forms.NumberInput(attrs={'class': FIELD_CLS, 'min': 1}),
            'has_private_bathroom': forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
            'has_ac': forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        price_fields = ['price_hour', 'price_day', 'price_night', 'price_month']
        prices = [cleaned_data.get(field) for field in price_fields]

        if not any(price is not None and price > 0 for price in prices):
            raise forms.ValidationError('Defina pelo menos um preço válido: por hora, dia, noite ou mês.')

        minimum_hours = cleaned_data.get('minimum_hours') or 1
        price_hour = cleaned_data.get('price_hour')
        if price_hour and minimum_hours < 1:
            self.add_error('minimum_hours', 'O mínimo de horas deve ser pelo menos 1.')

        return cleaned_data


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
            'property': forms.Select(attrs={'class': FIELD_CLS}),
            'room': forms.Select(attrs={'class': FIELD_CLS}),
            'image': forms.FileInput(attrs={'class': FIELD_CLS, 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Quarto principal, recepção, casa de banho'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image:
            if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(f'A imagem deve ter no máximo {MAX_IMAGE_SIZE_MB}MB.')

            if not getattr(image, 'content_type', '').startswith('image/'):
                raise forms.ValidationError('Apenas ficheiros de imagem são permitidos.')

        return image


class MultiplePropertyPhotoForm(forms.Form):
    room = forms.ModelChoiceField(
        label='Associar a quarto/unidade',
        queryset=Room.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': FIELD_CLS}),
        help_text='Opcional. Use quando as fotos pertencerem a um quarto específico.'
    )
    images = MultipleFileField(
        label='Fotografias',
        required=True,
        help_text='Seleccione várias imagens reais e nítidas. Cada uma deve ter no máximo 5MB.'
    )
    caption = forms.CharField(
        label='Legenda comum',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': FIELD_CLS, 'placeholder': 'Ex: Fotos do quarto executivo'}),
        help_text='Será aplicada às fotos carregadas. Pode deixar vazio.'
    )
    set_first_as_main = forms.BooleanField(
        label='Definir a primeira foto como principal',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-5 w-5 rounded border-slate-300 text-blue-700'}),
    )

    def __init__(self, *args, **kwargs):
        property_obj = kwargs.pop('property_obj', None)
        super().__init__(*args, **kwargs)
        if property_obj is not None:
            self.fields['room'].queryset = property_obj.rooms.all()

    def clean_images(self):
        images = self.cleaned_data.get('images') or []
        if not images:
            raise forms.ValidationError('Seleccione pelo menos uma fotografia.')
        return images
