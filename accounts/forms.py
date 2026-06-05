from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.text import slugify

from .models import ClientProfile, OwnerProfile

INPUT_CLASS = 'w-full px-4 py-3 rounded-xl border border-slate-300'


def set_model_field_if_exists(instance, field_name, value):
    """
    Define um campo apenas se ele existir no modelo.
    Isto evita erro caso ClientProfile ou OwnerProfile tenham campos diferentes.
    """
    if value in [None, '']:
        return

    model_fields = [field.name for field in instance._meta.fields]

    if field_name in model_fields:
        setattr(instance, field_name, value)


def generate_unique_username(email='', phone='', first_name='', fallback='guest258'):
    """Gera um username simples quando o utilizador não quiser criar um."""
    base = ''
    if email and '@' in email:
        base = email.split('@')[0]
    elif phone:
        base = ''.join(ch for ch in phone if ch.isdigit())[-9:]
    elif first_name:
        base = first_name

    base = slugify(base).replace('-', '_') or fallback
    base = base[:80]
    candidate = base
    counter = 1

    while User.objects.filter(username__iexact=candidate).exists():
        counter += 1
        candidate = f'{base}_{counter}'[:150]

    return candidate


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='E-mail ou utilizador',
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Digite o seu e-mail ou utilizador',
            'autocomplete': 'username',
        })
    )

    password = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'A sua palavra-passe',
            'autocomplete': 'current-password',
        })
    )

    error_messages = {
        'invalid_login': 'Não conseguimos entrar com estes dados. Confirme o e-mail/utilizador e a palavra-passe.',
        'inactive': 'Esta conta está inactiva.',
    }


class SimpleRegistrationMixin:
    """Cadastro simplificado: username opcional, confirmação de password opcional."""

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Já existe uma conta com este nome de utilizador. Pode deixar este campo vazio e nós criamos um automaticamente.')
        return username

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail. Use “Esqueci a palavra-passe” para recuperar o acesso.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password2 and password1 and password1 != password2:
            raise forms.ValidationError('As palavras-passe não coincidem.')
        return password2 or password1

    def _prepare_user(self, user):
        if not user.username:
            user.username = generate_unique_username(
                email=self.cleaned_data.get('email', ''),
                phone=self.cleaned_data.get('phone', ''),
                first_name=self.cleaned_data.get('first_name', ''),
            )
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.is_active = True
        return user


class ClientRegistrationForm(SimpleRegistrationMixin, UserCreationForm):
    first_name = forms.CharField(
        label='Nome',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'O seu nome',
            'autocomplete': 'given-name',
        })
    )

    last_name = forms.CharField(
        label='Apelido',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'family-name',
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'email@exemplo.com',
            'autocomplete': 'email',
        })
    )

    phone = forms.CharField(
        label='Telefone',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': '+258 84 000 0000',
            'autocomplete': 'tel',
        })
    )

    username = forms.CharField(
        label='Nome de utilizador',
        max_length=150,
        required=False,
        help_text='Opcional. Se deixar vazio, a +258 Guest cria um automaticamente.',
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'username',
        })
    )

    password1 = forms.CharField(
        label='Palavra-passe',
        help_text='Mínimo de 4 caracteres. Pode usar números ou letras simples.',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Mínimo 4 caracteres',
            'minlength': '4',
            'autocomplete': 'new-password',
        })
    )

    password2 = forms.CharField(
        label='Confirmar palavra-passe',
        required=False,
        help_text='Opcional. Preencha apenas se quiser confirmar.',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'new-password',
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'username',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user = self._prepare_user(user)

        if commit:
            user.save()
            profile, created = ClientProfile.objects.get_or_create(user=user)
            phone = self.cleaned_data.get('phone')
            set_model_field_if_exists(profile, 'phone', phone)
            set_model_field_if_exists(profile, 'telefone', phone)
            set_model_field_if_exists(profile, 'contact', phone)
            set_model_field_if_exists(profile, 'contacto', phone)
            profile.save()

        return user


class OwnerRegistrationForm(SimpleRegistrationMixin, UserCreationForm):
    first_name = forms.CharField(
        label='Nome',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'O seu nome',
            'autocomplete': 'given-name',
        })
    )

    last_name = forms.CharField(
        label='Apelido',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'family-name',
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'email@exemplo.com',
            'autocomplete': 'email',
        })
    )

    phone = forms.CharField(
        label='Telefone',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': '+258 84 000 0000',
            'autocomplete': 'tel',
        })
    )

    company_name = forms.CharField(
        label='Nome do alojamento/empresa',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
        })
    )

    username = forms.CharField(
        label='Nome de utilizador',
        max_length=150,
        required=False,
        help_text='Opcional. Se deixar vazio, a +258 Guest cria um automaticamente.',
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'username',
        })
    )

    password1 = forms.CharField(
        label='Palavra-passe',
        help_text='Mínimo de 4 caracteres. Pode usar números ou letras simples.',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Mínimo 4 caracteres',
            'minlength': '4',
            'autocomplete': 'new-password',
        })
    )

    password2 = forms.CharField(
        label='Confirmar palavra-passe',
        required=False,
        help_text='Opcional. Preencha apenas se quiser confirmar.',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'new-password',
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'company_name',
            'username',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user = self._prepare_user(user)

        if commit:
            user.save()
            profile, created = OwnerProfile.objects.get_or_create(user=user)
            phone = self.cleaned_data.get('phone')
            company_name = self.cleaned_data.get('company_name')

            set_model_field_if_exists(profile, 'phone', phone)
            set_model_field_if_exists(profile, 'telefone', phone)
            set_model_field_if_exists(profile, 'contact', phone)
            set_model_field_if_exists(profile, 'contacto', phone)

            set_model_field_if_exists(profile, 'company_name', company_name)
            set_model_field_if_exists(profile, 'business_name', company_name)
            set_model_field_if_exists(profile, 'nome_empresa', company_name)
            set_model_field_if_exists(profile, 'establishment_name', company_name)

            profile.save()

        return user


class ClientProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nome',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS
        })
    )

    last_name = forms.CharField(
        label='Apelido',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS
        })
    )

    class Meta:
        model = ClientProfile
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            if 'border' not in existing_class:
                field.widget.attrs['class'] = INPUT_CLASS

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')

            if commit:
                self.user.save()

        if commit:
            profile.save()

        return profile


class OwnerKYCForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nome',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    last_name = forms.CharField(
        label='Apelido',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS})
    )
    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS})
    )

    class Meta:
        model = OwnerProfile
        fields = [
            'business_name',
            'document_type',
            'document_number',
            'nuit',
            'payment_phone',
            'payout_mpesa_phone',
            'payout_emola_phone',
            'payout_bank_details',
            'identity_document',
            'nuit_document',
            'ownership_proof',
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'document_type': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'BI, DIRE, Passaporte, Alvará, etc.'}),
            'document_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'nuit': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'payment_phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+258 84/85/86/87 xxx xxxx'}),
            'payout_mpesa_phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'payout_emola_phone': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'payout_bank_details': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4, 'placeholder': 'Banco, titular, NIB/conta, observações.'}),
            'identity_document': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': '.pdf,image/*'}),
            'nuit_document': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': '.pdf,image/*'}),
            'ownership_proof': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': '.pdf,image/*'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean(self):
        cleaned = super().clean()
        has_payout = any([
            cleaned.get('payment_phone'),
            cleaned.get('payout_mpesa_phone'),
            cleaned.get('payout_emola_phone'),
            cleaned.get('payout_bank_details'),
        ])
        if not has_payout:
            raise forms.ValidationError('Informe pelo menos uma forma de liquidação: M-Pesa, e-Mola ou dados bancários.')
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.verification_status in {'unverified', 'rejected'}:
            profile.verification_status = 'pending'
        elif profile.verification_status != 'verified':
            profile.verification_status = 'in_review'

        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            if commit:
                self.user.save()

        if commit:
            profile.save()
        return profile


class Guest258PasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='E-mail da conta',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Digite o e-mail usado na +258 Guest',
            'autocomplete': 'email',
        })
    )


class Guest258SetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='Nova palavra-passe',
        help_text='Mínimo de 4 caracteres.',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Mínimo 4 caracteres',
            'minlength': '4',
            'autocomplete': 'new-password',
        }),
        strip=False,
    )
    new_password2 = forms.CharField(
        label='Confirmar nova palavra-passe',
        required=False,
        help_text='Opcional. Preencha apenas se quiser confirmar.',
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Opcional',
            'autocomplete': 'new-password',
        }),
        strip=False,
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password2 and password1 and password1 != password2:
            raise forms.ValidationError('As palavras-passe não coincidem.')
        return password2 or password1
