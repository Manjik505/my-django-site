import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adaptation_project.settings')
django.setup()

from django.contrib.auth.models import User


USERNAME = "admin"       
EMAIL = "admin@example.com"   
PASSWORD = "admin"   



if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
    print(f"✅ Суперпользователь '{USERNAME}' создан!")
else:
    print(f"⚠️ Пользователь '{USERNAME}' уже существует.")
