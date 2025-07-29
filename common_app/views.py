from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, PetForm
from .models import Pet
from photo_board_app.models import Post
from weight_tracker_app.models import Weight
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from insurance_app.models import PetProfile

# Create your views here.

@login_required
def index(request):
    context = {}
    if request.user.is_authenticated:
        pets = Pet.objects.filter(owner=request.user)
        recent_posts = Post.objects.filter(image__isnull=False, pet__owner=request.user).order_by('-created_at')[:12]
        context.update({
            'pets': pets,
            'recent_posts': recent_posts,
            'pet_form': PetForm(),
        })
    return render(request, 'common_app/index.html', context)

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            # 여러 마리 고양이 정보 저장
            pet_idx = 0
            while True:
                name = request.POST.get(f'pet_name_{pet_idx}')
                breed = request.POST.get(f'pet_breed_{pet_idx}')
                birth_date = request.POST.get(f'pet_birth_date_{pet_idx}')
                gender = request.POST.get(f'pet_gender_{pet_idx}')
                neutered = request.POST.get(f'pet_neutered_{pet_idx}')
                weight = request.POST.get(f'pet_weight_{pet_idx}')
                notes = request.POST.get(f'pet_notes_{pet_idx}')
                image = request.FILES.get(f'pet_image_{pet_idx}')
                if not name:
                    break
                pet = Pet.objects.create(
                    owner=user,
                    name=name,
                    pet_type='cat',
                    breed=breed,
                    birth_date=birth_date,
                    weight=weight or None,
                    image=image,
                )
                # PetProfile 자동 생성
                if not PetProfile.objects.filter(user=user, name=name, breed=breed, birth_date=birth_date).exists():
                    PetProfile.objects.create(
                        user=user,
                        name=name,
                        pet_type='cat',
                        breed=breed,
                        birth_date=birth_date,
                        weight=weight or None,
                        gender=gender or 'male',
                        is_neutered=neutered == 'on',
                    )
                pet_idx += 1
            messages.success(request, '회원가입이 완료되었습니다!')
            return redirect('login')
    else:
        user_form = UserRegisterForm()
    # pet_form 추가
    pet_form = PetForm()
    return render(request, 'common_app/register.html', {
        'user_form': user_form,
        'pet_form': pet_form,
        'pet_breeds': Pet.CAT_BREEDS,
    })

@login_required
def pet_edit(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    latest_weight = Weight.objects.filter(pet=pet).order_by('-date').first()
    initial = {}
    if latest_weight:
        initial['weight'] = latest_weight.weight
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            pet = form.save()
            if not PetProfile.objects.filter(user=request.user, name=pet.name, breed=pet.breed, birth_date=pet.birth_date).exists():
                PetProfile.objects.create(
                    user=request.user,
                    name=pet.name,
                    pet_type='cat',
                    breed=pet.breed,
                    birth_date=pet.birth_date,
                    weight=pet.weight,
                    gender=pet.gender,
                    is_neutered=pet.neutered,
                )
            messages.success(request, '반려동물 정보가 수정되었습니다.')
            return redirect('index')
    else:
        form = PetForm(instance=pet, initial=initial)
    return render(request, 'common_app/pet_edit.html', {'form': form, 'pet': pet})

@login_required
def pet_update(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, '반려동물 정보가 수정되었습니다.')
            return redirect('index')
    return redirect('pets:edit', pet_id=pet_id)

@login_required
def pet_register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        breed = request.POST.get('breed')
        birth_date = request.POST.get('birth_date')
        gender = request.POST.get('gender')
        neutered = request.POST.get('neutered')
        weight = request.POST.get('weight')
        notes = request.POST.get('notes')
        image = request.FILES.get('image')
        pet = Pet.objects.create(
            owner=request.user,
            name=name,
            pet_type='cat',
            breed=breed,
            birth_date=birth_date,
            weight=weight or None,
            image=image,
        )
        # PetProfile 자동 생성
        if not PetProfile.objects.filter(user=request.user, name=name, breed=breed, birth_date=birth_date).exists():
            PetProfile.objects.create(
                user=request.user,
                name=name,
                pet_type='cat',
                breed=breed,
                birth_date=birth_date,
                weight=weight or None,
                gender=gender or 'male',
                is_neutered=neutered == 'on',
            )
        messages.success(request, '반려동물이 등록되었습니다.')
        return redirect('index')
    else:
        form = PetForm()
    return render(request, 'common_app/pet_register.html', {'form': form})

@login_required
def pet_delete(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        pet.delete()
        return redirect('index')
    return render(request, 'common_app/pet_confirm_delete.html', {'pet': pet})

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        
        # 기본 정보 업데이트
        user.email = request.POST.get('email', user.email)
        
        # 소셜 로그인 사용자인지 확인
        is_social_user = user.socialaccount_set.exists()
        
        # 비밀번호 변경 처리 (일반 로그인 사용자만)
        password_changed = False
        if not is_social_user:
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if current_password and new_password1 and new_password2:
                if new_password1 == new_password2:
                    if user.check_password(current_password):
                        user.set_password(new_password1)
                        password_changed = True
                    else:
                        messages.error(request, '현재 비밀번호가 올바르지 않습니다.')
                        return render(request, 'common_app/profile.html')
                else:
                    messages.error(request, '새 비밀번호가 일치하지 않습니다.')
                    return render(request, 'common_app/profile.html')
        
        try:
            user.save()
            if password_changed:
                update_session_auth_hash(request, user)
                messages.success(request, '프로필 정보와 비밀번호가 성공적으로 변경되었습니다.')
            else:
                if is_social_user:
                    messages.success(request, '이메일 정보가 성공적으로 변경되었습니다.')
                else:
                    messages.success(request, '프로필 정보가 성공적으로 변경되었습니다.')
        except Exception as e:
            messages.error(request, '정보 저장 중 오류가 발생했습니다.')
        
        return redirect('common_app:profile')
    
    return render(request, 'common_app/profile.html')

def kakao_callback(request):
    import requests
    from django.contrib.auth import login
    from django.contrib.auth.models import User
    from allauth.socialaccount.models import SocialAccount
    from django.http import HttpResponse
    
    # 에러 처리
    error = request.GET.get('error')
    if error:
        print(f"DEBUG: Kakao login error: {error}")
        return redirect('login')
    
    code = request.GET.get('code')
    print(f"DEBUG: Received code: {code[:20]}..." if code else "No code")
    
    if not code:
        print("DEBUG: No code found, redirecting to login")
        return redirect('login')
    
    try:
        # 카카오에서 토큰 획득
        token_url = 'https://kauth.kakao.com/oauth/token'
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': '60e6a9eaa8547966f54c5db6a27481d9',
            'client_secret': 'NcTLzquKaSmCPaDIug3RHBfpl7iJDhPH',
            'redirect_uri': 'http://localhost:8000/kakao/callback/',
            'code': code,
        }
        
        print("DEBUG: Requesting token from Kakao...")
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            error_msg = token_json.get('error_description', 'Unknown error')
            print(f"DEBUG: Token error: {error_msg}")
            return redirect('login')
        
        access_token = token_json['access_token']
        print("DEBUG: Access token obtained successfully")
        
        # 카카오에서 사용자 정보 획득
        user_info_url = 'https://kapi.kakao.com/v2/user/me'
        user_info_response = requests.get(
            user_info_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_info = user_info_response.json()
        
        kakao_id = user_info['id']
        nickname = user_info.get('properties', {}).get('nickname', f'kakao_user_{kakao_id}')
        email = user_info.get('kakao_account', {}).get('email', '')
        
        print(f"DEBUG: Kakao user info - ID: {kakao_id}, Nickname: {nickname}, Email: {email}")
        print(f"DEBUG: Full kakao_account: {user_info.get('kakao_account', {})}")
        
        print(f"DEBUG: Kakao user - ID: {kakao_id}, Nickname: {nickname}")
        
        # 사용자 확인 또는 생성
        is_new_user = False
        try:
            social_account = SocialAccount.objects.get(provider='kakao', uid=str(kakao_id))
            user = social_account.user
            print(f"DEBUG: Existing user found: {user.username}")
            
            # 기존 사용자의 정보 업데이트
            updated = False
            
            # username이 kakao_숫자 형태라면 닉네임으로 업데이트
            if user.username.startswith('kakao_') and user.username != nickname:
                base_username = nickname if nickname else f'kakao_user_{kakao_id}'
                username = base_username
                counter = 1
                while User.objects.exclude(id=user.id).filter(username=username).exists():
                    username = f'{base_username}_{counter}'
                    counter += 1
                
                user.username = username
                user.first_name = nickname
                updated = True
                print(f"DEBUG: Updated username to: {username}")
            
            # 이메일이 비어있거나 다르면 업데이트
            if email and user.email != email:
                user.email = email
                updated = True
                print(f"DEBUG: Updated email to: {email}")
            
            if updated:
                user.save()
                
        except SocialAccount.DoesNotExist:
            print(f"DEBUG: Creating new user for kakao_id: {kakao_id}")
            is_new_user = True
            
            # 새 사용자 생성
            # 닉네임이 중복될 수 있으므로 고유한 username 생성
            base_username = nickname if nickname else f'kakao_user_{kakao_id}'
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}_{counter}'
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=nickname
            )
            
            # SocialAccount 생성
            SocialAccount.objects.create(
                user=user,
                provider='kakao',
                uid=str(kakao_id),
                extra_data=user_info
            )
            print(f"DEBUG: New user created: {user.username}")
        
        # 로그인 처리
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        print(f"DEBUG: User logged in: {user.username}")
        
        # 새 사용자라면 추가 정보 입력 페이지로, 기존 사용자라면 홈으로
        if is_new_user:
            return redirect('pet_register')  # 펫 등록 페이지로 리다이렉트
        else:
            return redirect('index')
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect('login')

# 로그아웃 후 로그인 페이지로 리다이렉트하는 커스텀 뷰
def custom_logout_view(request):
    logout(request)
    return redirect('login')
