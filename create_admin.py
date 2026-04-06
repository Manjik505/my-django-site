import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adaptation_project.settings')
django.setup()

from django.contrib.auth.models import User

# Удаляем старого, если есть
User.objects.filter(username="admin").delete()

# Создаём нового
User.objects.create_superuser("admin", "admin@example.com", "admin123")
print("✅ Админ создан! Логин: admin, Пароль: admin123")
