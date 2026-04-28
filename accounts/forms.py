from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import ClientProfile, OwnerProfile


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


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Utilizador ou e-mail',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Username ou e-mail'
        })
    )

    password = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Palavra-passe'
        })
    )


class ClientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nome',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Nome'
        })
    )

    last_name = forms.CharField(
        label='Apelido',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Apelido'
        })
    )

    username = forms.CharField(
        label='Nome de utilizador',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Ex: cliente1'
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'email@exemplo.com'
        })
    )

    phone = forms.CharField(
        label='Telefone',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': '+258 84 000 0000'
        })
    )

    password1 = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Palavra-passe'
        })
    )

    password2 = forms.CharField(
        label='Confirmar palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Confirmar palavra-passe'
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'password1',
            'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')

        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Já existe uma conta com este nome de utilizador.')

        return username

    def save(self, commit=True):
        """
        UserCreationForm já usa set_password correctamente.
        Portanto a password fica gravada como hash pbkdf2_sha256.
        """
        user = super().save(commit=False)

        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.is_active = True

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


class OwnerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nome',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Nome'
        })
    )

    last_name = forms.CharField(
        label='Apelido',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Apelido'
        })
    )

    username = forms.CharField(
        label='Nome de utilizador',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Ex: proprietario1'
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'email@exemplo.com'
        })
    )

    phone = forms.CharField(
        label='Telefone',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': '+258 84 000 0000'
        })
    )

    company_name = forms.CharField(
        label='Nome da empresa / estabelecimento',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Nome comercial'
        })
    )

    password1 = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Palavra-passe'
        })
    )

    password2 = forms.CharField(
        label='Confirmar palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Confirmar palavra-passe'
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'company_name',
            'password1',
            'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')

        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Já existe uma conta com este nome de utilizador.')

        return username

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.is_active = True

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
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
        })
    )

    last_name = forms.CharField(
        label='Apelido',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
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
                field.widget.attrs['class'] = 'w-full px-4 py-3 rounded-xl border border-slate-300'

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
