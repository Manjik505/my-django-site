from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Avg, Max
from django.http import JsonResponse, HttpResponse
from .models import Course, Question, Result, UserProgress, Profile
from django.contrib.auth.models import User
import json
from django.core import serializers

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            password = request.POST.get('password1')
            profile, created = Profile.objects.get_or_create(user=user)
            profile.plain_password = password
            profile.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('profile')
    else:
        form = UserCreationForm()
    return render(request, 'courses/register.html', {'form': form})

@login_required
def profile(request):
    all_results = Result.objects.filter(user=request.user).order_by('-created_at')
    
    unique_results = {}
    for result in all_results:
        if result.course_id not in unique_results:
            unique_results[result.course_id] = result
    
    user_results = list(unique_results.values())
    user_results.sort(key=lambda x: x.created_at, reverse=True)
    
    stats = {
        'total': len(user_results),
        'avg': round(sum(r.score for r in user_results) / len(user_results)) if user_results else 0,
        'best': max((r.score for r in user_results), default=0),
    }
    
    completed_count = UserProgress.objects.filter(user=request.user, completed=True).count()
    in_progress_count = UserProgress.objects.filter(user=request.user, in_progress=True).count()
    total_courses = Course.objects.count()
    not_started = total_courses - completed_count - in_progress_count
    
    recent = user_results[:5]
    
    profile, created = Profile.objects.get_or_create(user=request.user)
    avatar = profile.avatar
    
    context = {
        'stats': stats,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'not_started': not_started,
        'recent': recent,
        'avatar': avatar,
    }
    return render(request, 'courses/profile.html', context)

@login_required
def courses_list(request):
    courses = Course.objects.all().prefetch_related('questions')
    
    progress_dict = {}
    for p in UserProgress.objects.filter(user=request.user):
        progress_dict[p.course_id] = p
    
    filter_type = request.GET.get('filter', 'all')
    category = request.GET.get('category', 'all')
    search = request.GET.get('search', '')
    
    if category != 'all':
        courses = courses.filter(category=category)
    
    if search and search.strip() != '':
        courses = courses.filter(title__icontains=search)
    
    if filter_type == 'completed':
        course_ids = [p.course_id for p in UserProgress.objects.filter(user=request.user, completed=True)]
        courses = courses.filter(id__in=course_ids)
    elif filter_type == 'in-progress':
        course_ids = [p.course_id for p in UserProgress.objects.filter(user=request.user, in_progress=True)]
        courses = courses.filter(id__in=course_ids)
    elif filter_type == 'not-started':
        completed_ids = [p.course_id for p in UserProgress.objects.filter(user=request.user)]
        courses = courses.exclude(id__in=completed_ids)
    
    def get_item(dictionary, key):
        return dictionary.get(key)
    
    context = {
        'courses': courses,
        'progress_dict': progress_dict,
        'current_filter': filter_type,
        'current_category': category,
        'search_query': search,
        'categories': Course.CATEGORY_CHOICES,
        'get_item': get_item,
    }
    return render(request, 'courses/courses.html', context)

@login_required
def course_theory(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'courses/theory.html', {'course': course})

@login_required
def start_test(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = course.questions.all()
    
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={'in_progress': True}
    )
    if not created and not progress.completed:
        progress.in_progress = True
        progress.save()
    
    questions_data = []
    for q in questions:
        questions_data.append({
            'id': q.id,
            'text': q.text,
            'options': q.get_options(),
            'correct': q.correct
        })
    
    request.session['current_test'] = {
        'course_id': course.id,
        'course_title': course.title,
        'questions': questions_data,
        'total': questions.count()
    }
    
    return render(request, 'courses/test.html', {
        'course': course,
        'total': questions.count(),
        'questions_json': json.dumps(questions_data),
    })

@login_required
def finish_test(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            answers = data.get('answers', [])
            score = data.get('score', 0)
            correct = data.get('correct', 0)
            
            test_data = request.session.get('current_test', {})
            course_id = test_data.get('course_id')
            
            if course_id:
                course = get_object_or_404(Course, id=course_id)
                
                Result.objects.create(
                    user=request.user,
                    course=course,
                    score=score,
                    correct=correct,
                    total=len(answers)
                )
                
                progress, created = UserProgress.objects.get_or_create(
                    user=request.user,
                    course=course
                )
                if score >= 70:
                    progress.completed = True
                    progress.in_progress = False
                else:
                    progress.completed = False
                    progress.in_progress = False
                progress.save()
                
                if 'current_test' in request.session:
                    del request.session['current_test']
                
                request.session['last_result'] = {
                    'score': score,
                    'correct': correct,
                    'total': len(answers),
                    'course_id': course.id,
                    'course_title': course.title
                }
                
                return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    last_result = request.session.get('last_result', {})
    course = None
    if last_result.get('course_id'):
        course = get_object_or_404(Course, id=last_result['course_id'])
    else:
        course = Course.objects.first()
    
    score = last_result.get('score', 0)
    if score >= 80:
        message = 'Отлично! Вы отлично усвоили материал!'
    elif score >= 60:
        message = 'Хороший результат! Есть что подтянуть.'
    else:
        message = 'Стоит повторить материал. Обратитесь к наставнику.'
    
    return render(request, 'courses/result.html', {
        'score': score,
        'correct': last_result.get('correct', 0),
        'total': last_result.get('total', 0),
        'course': course,
        'message': message
    })

def page_view(request, page_name):
    pages = {
        'news': {
            'title': 'Новости', 
            'content': '''
                <div class="info-row">
                    <strong>Новый сотрудник месяца!</strong><br>
                    Поздравляем Ивана Петрова с отличными результатами!<br>
                    <small>30 марта 2026</small>
                </div>
                <div class="info-row">
                    <strong>Запуск программы наставничества</strong><br>
                    Каждому новому сотруднику будет назначен наставник.<br>
                    <small>25 марта 2026</small>
                </div>
                <div class="info-row">
                    <strong>Обновление CRM-системы</strong><br>
                    Добавлены новые функции для удобной работы.<br>
                    <small>20 марта 2026</small>
                </div>
            '''
        },
        'events': {
            'title': 'Мероприятия', 
            'content': '''
                <div class="info-row">
                    <strong>Весенний корпоратив</strong><br>
                    15 апреля 2026 | 18:00 | Ресторан "Прага"
                </div>
                <div class="info-row">
                    <strong>Вебинар "Эффективная адаптация"</strong><br>
                    5 апреля 2026 | 11:00 | Zoom
                </div>
                <div class="info-row">
                    <strong>Спортивный день</strong><br>
                    12 апреля 2026 | 10:00 | Городской парк
                </div>
            '''
        },
        'about': {
            'title': 'О нас', 
            'content': '''
                <p>Наша компания основана в 2015 году. За это время мы выросли из небольшого стартапа в лидера рынка.</p>
                <h3>Наши ценности:</h3>
                <ul>
                    <li>Честность и открытость</li>
                    <li>Инновации и развитие</li>
                    <li>Командная работа</li>
                    <li>Ориентация на результат</li>
                </ul>
                <p>Наша миссия: помогать людям и бизнесу достигать новых высот через технологии и человеческий потенциал.</p>
            '''
        },
        'support': {
            'title': 'Поддержка', 
            'content': '''
                <p>Телефон: +7 (495) 123-45-67<br>
                Email: support@company.ru<br>
                Режим работы: Пн-Пт 9:00-18:00</p>
                <p>Чат-поддержка: в корпоративном мессенджере<br>
                IT-поддержка: it-help@company.ru</p>
            '''
        }
    }
    
    page = pages.get(page_name)
    if not page:
        page = {'title': 'Страница не найдена', 'content': '<p>Страница в разработке</p>'}
    
    return render(request, 'courses/page.html', {'title': page['title'], 'content': page['content']})

# ============ API ДЛЯ АВАТАРКИ ============
@login_required
def upload_avatar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            avatar_data = data.get('avatar')
            if avatar_data:
                profile, created = Profile.objects.get_or_create(user=request.user)
                profile.avatar = avatar_data
                profile.save()
                return JsonResponse({'success': True})
        except:
            pass
    return JsonResponse({'success': False})

@login_required
def remove_avatar(request):
    if request.method == 'POST':
        try:
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.avatar = None
            profile.save()
            return JsonResponse({'success': True})
        except:
            pass
    return JsonResponse({'success': False})

# ============ ЧАТ С ПОДДЕРЖКОЙ ============
def support_chat(request):
    return render(request, 'courses/support_chat.html')

# ============ ВОССТАНОВЛЕНИЕ ПАРОЛЯ ============
def forgot_password(request):
    user_password = None
    username = None
    email_input = ''
    login_input = ''
    found = False
    error_message = None
    
    if request.method == 'POST':
        login_input = request.POST.get('login', '').strip()
        email_input = request.POST.get('email', '').strip()
        
        user = None
        
        if login_input:
            try:
                user = User.objects.get(username=login_input)
            except User.DoesNotExist:
                pass
        
        if not user and email_input:
            try:
                user = User.objects.get(email=email_input)
            except User.DoesNotExist:
                pass
        
        if user:
            try:
                profile = Profile.objects.get(user=user)
                user_password = profile.plain_password
                
                if user_password and user_password.startswith('pbkdf2_sha256'):
                    error_message = 'Пароль сохранён в зашифрованном виде. Обратитесь к администратору.'
                    user_password = None
                else:
                    username = user.username
                    email_input = user.email
                    found = True
            except Profile.DoesNotExist:
                pass
    
    return render(request, 'courses/forgot_password.html', {
        'found': found,
        'username': username,
        'email': email_input,
        'login': login_input,
        'password': user_password,
        'error_message': error_message,
    })

# ============ API ДЛЯ ЧАТА (ПОЛУЧЕНИЕ ПАРОЛЯ) ============
def api_get_user_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            login = data.get('login', '').strip()
            email = data.get('email', '').strip()
            
            user = None
            
            if login:
                try:
                    user = User.objects.get(username=login)
                except User.DoesNotExist:
                    pass
            
            if not user and email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass
            
            if not user:
                return JsonResponse({'success': False, 'error': 'Пользователь не найден'})
            
            profile = Profile.objects.get(user=user)
            password = profile.plain_password
            
            if not password or password.startswith('pbkdf2_sha256'):
                return JsonResponse({'success': False, 'error': 'Пароль не сохранён в открытом виде. Обратитесь к администратору.'})
            
            return JsonResponse({
                'success': True,
                'username': user.username,
                'email': user.email,
                'password': password
            })
        except Profile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Профиль не найден'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})

# ============ ЭКСПОРТ БАЗЫ ДАННЫХ ============
def export_full_database(request):
    if not request.user.is_superuser:
        return HttpResponse("Доступ запрещен", status=403)
    
    data = []
    models_to_export = [User, Profile, Course, Question, Result, UserProgress]
    
    for model in models_to_export:
        queryset = model.objects.all().order_by('pk')
        data.extend(serializers.serialize('json', queryset))
    
    full_data = f"[{','.join(data)}]"
    
    response = HttpResponse(full_data, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="full_site_database.json"'
    return response
