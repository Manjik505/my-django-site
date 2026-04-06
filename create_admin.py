import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adaptation_project.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin")
    print("✅ Админ создан")
else:
    print("⚠️ Админ уже существует")
