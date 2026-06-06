MOZGUEST - CHECKLIST DE PRODUCAO

1) Instalar dependencias:
   pip install -r requirements.txt

2) Variaveis de ambiente obrigatorias:
   DJANGO_SECRET_KEY
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS
   DJANGO_CSRF_TRUSTED_ORIGINS

3) Para PostgreSQL em producao:
   DATABASE_URL
   DB_SSL_REQUIRE=True

4) Preparar base de dados:
   python manage.py migrate
   python manage.py createsuperuser

5) Static files:
   python manage.py collectstatic --noinput

6) Arranque local:
   python manage.py runserver

7) Arranque producao:
   gunicorn config.wsgi:application

8) PWA:
   Confirmar se /service-worker.js e /static/manifest.json abrem no dominio HTTPS.

9) Media files:
   Em deploy real, configurar armazenamento persistente para /media/ ou usar S3/Cloudinary.
