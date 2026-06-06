from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Permite autenticação com username ou e-mail, mantendo password hashing normal do Django."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get(User.USERNAME_FIELD)
        if not login_value or not password:
            return None

        users = User.objects.filter(
            Q(username__iexact=login_value) | Q(email__iexact=login_value)
        ).order_by('id')

        # Se houver duplicidade de e-mail, privilegia username exacto.
        exact_username = users.filter(username__iexact=login_value).first()
        user = exact_username or users.first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        # Mitiga timing attacks quando o utilizador não existe.
        User().set_password(password)
        return None
