import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adaptation_project.settings')
django.setup()

from django.contrib.auth.models import User

# Создаём админа
username = "admin"
password = "admin"
email = "admin@example.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"✅ Админ {username} создан!")
else:
    print(f"⚠️ Админ {username} уже есть, пробуем войти")
    
    # Сбрасываем пароль, если админ уже есть
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"✅ Пароль для {username} обновлён!")
