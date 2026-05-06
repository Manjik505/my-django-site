from django.urls import path
from . import views

urlpatterns = [
    path('', views.courses_list, name='home'),
    path('profile/', views.profile, name='profile'),
    path('courses/', views.courses_list, name='courses'),
    path('course/<int:course_id>/', views.course_theory, name='course_theory'),
    path('course/<int:course_id>/test/', views.start_test, name='start_test'),
    path('finish-test/', views.finish_test, name='finish_test'),
    path('register/', views.register, name='register'),
    path('page/<str:page_name>/', views.page_view, name='page'),
    path('api/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('api/remove-avatar/', views.remove_avatar, name='remove_avatar'),
    path('support-chat/', views.support_chat, name='support_chat'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('export/', views.export_full_database, name='export_db'),
    path('api/get-user-password/', views.api_get_user_password, name='api_get_user_password'),
]
