import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria um backup lógico do +258 Guest: base de dados em JSON, manifesto de media e cópia SQLite quando aplicável.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='backups', help='Pasta onde o backup será gravado.')
        parser.add_argument('--include-media', action='store_true', help='Copia também a pasta media quando o storage é local.')

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_root = Path(options['output_dir']).resolve() / f'mozguest-backup-{timestamp}'
        backup_root.mkdir(parents=True, exist_ok=True)

        data_file = backup_root / 'database.json'
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            '--exclude', 'contenttypes',
            '--exclude', 'auth.permission',
            output=str(data_file),
            verbosity=0,
        )

        manifest = {
            'created_at': timestamp,
            'version': getattr(settings, 'MOZGUEST_VERSION', 'unknown'),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'storage_backend': getattr(settings, 'MOZGUEST_STORAGE_BACKEND', 'local'),
            'media_files': [],
        }

        media_root = Path(getattr(settings, 'MEDIA_ROOT', 'media'))
        if media_root.exists():
            for path in media_root.rglob('*'):
                if path.is_file():
                    manifest['media_files'].append(str(path.relative_to(media_root)))
            if options['include_media'] and getattr(settings, 'MOZGUEST_STORAGE_BACKEND', 'local') == 'local':
                shutil.copytree(media_root, backup_root / 'media', dirs_exist_ok=True)

        db_name = settings.DATABASES['default'].get('NAME')
        if settings.DATABASES['default']['ENGINE'].endswith('sqlite3') and db_name and Path(db_name).exists():
            shutil.copy2(db_name, backup_root / 'db.sqlite3')

        manifest_file = backup_root / 'manifest.json'
        manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')

        checksums = []
        for path in sorted(backup_root.rglob('*')):
            if path.is_file():
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                checksums.append(f'{digest}  {path.relative_to(backup_root)}')
        (backup_root / 'CHECKSUMS.sha256').write_text('\n'.join(checksums) + '\n', encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f'Backup criado em: {backup_root}'))
        self.stdout.write('Para restaurar dados JSON: python manage.py loaddata database.json')
