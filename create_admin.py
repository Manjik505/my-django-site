import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adaptation_project.settings')
django.setup()

from django.contrib.auth.models import User

# Удаляем старого пользователя если есть
User.objects.filter(username="admin").delete()
User.objects.filter(username="admin").delete()
User.objects.filter(username="newadmin").delete()

# Создаём нового админа
username = "admin"
password = "admin"
email = "admin@example.com"

user = User.objects.create_superuser(username, email, password)
print(f"✅ Суперпользователь '{username}' создан!")
print(f"🔐 Пароль: {password}")
