from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import OwnerProfile, ClientProfile


class ClientRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label='Nome completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Nome completo'
        })
    )

    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'email@exemplo.com'
        })
    )

    phone = forms.CharField(
        label='Telefone',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': '84 000 0000'
        })
    )

    city = forms.CharField(
        label='Cidade',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Maputo, Matola, Xai-Xai...'
        })
    )

    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Senha'
        })
    )

    password_confirm = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Confirmar senha'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('As senhas não coincidem.')

        return cleaned_data

    def save(self):
        full_name = self.cleaned_data['full_name']
        email = self.cleaned_data['email']
        phone = self.cleaned_data['phone']
        city = self.cleaned_data.get('city')
        password = self.cleaned_data['password']

        username = email.split('@')[0]
        original_username = username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f'{original_username}{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )

        ClientProfile.objects.create(
            user=user,
            phone=phone,
            city=city
        )

        return user


class OwnerRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label='Nome completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Nome completo'
        })
    )

    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'email@exemplo.com'
        })
    )

    phone = forms.CharField(
        label='Telefone',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': '84 000 0000'
        })
    )

    business_name = forms.CharField(
        label='Nome comercial',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Nome da guest house ou empresa'
        })
    )

    nuit = forms.CharField(
        label='NUIT',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'NUIT'
        })
    )

    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Senha'
        })
    )

    password_confirm = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Confirmar senha'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('As senhas não coincidem.')

        return cleaned_data

    def save(self):
        full_name = self.cleaned_data['full_name']
        email = self.cleaned_data['email']
        phone = self.cleaned_data['phone']
        business_name = self.cleaned_data.get('business_name')
        nuit = self.cleaned_data.get('nuit')
        password = self.cleaned_data['password']

        username = email.split('@')[0]
        original_username = username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f'{original_username}{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )

        OwnerProfile.objects.create(
            user=user,
            business_name=business_name,
            nuit=nuit,
            payment_phone=phone
        )

        return user


class ClientProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        label='Nome completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
        })
    )

    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'
        })
    )

    class Meta:
        model = ClientProfile
        fields = [
            'phone',
            'city',
            'neighbourhood',
            'preferred_contact',
        ]

        widgets = {
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'neighbourhood': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
            'preferred_contact': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-slate-300'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['full_name'].initial = self.user.get_full_name() or self.user.username
        self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)

        self.user.first_name = self.cleaned_data['full_name']
        self.user.email = self.cleaned_data['email']

        if commit:
            self.user.save()
            profile.save()

        return profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuário ou e-mail',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Usuário ou e-mail'
        })
    )

    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300',
            'placeholder': 'Senha'
        })
    )
