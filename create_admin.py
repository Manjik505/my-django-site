import os
import sys
import django

# Эта строка указывает на файл настроек вашего проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adaptation_project.settings')

# Эта функция подготавливает окружение Django для работы скрипта
def setup_django():
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    django.setup()

setup_django()

from django.contrib.auth import get_user_model

User = get_user_model()

# Данные для входа (вы можете их изменить, если хотите)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
ADMIN_EMAIL = "admin@example.com"

# Логика создания пользователя
user, created = User.objects.get_or_create(username=ADMIN_USERNAME, defaults={"email": ADMIN_EMAIL, "is_staff": True, "is_superuser": True})

if created:
    user.set_password(ADMIN_PASSWORD)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ СУПЕРПОЛЬЗОВАТЕЛЬ '{ADMIN_USERNAME}' УСПЕШНО СОЗДАН!")
else:
    print(f"ℹ️ Пользователь '{ADMIN_USERNAME}' уже существует.")
