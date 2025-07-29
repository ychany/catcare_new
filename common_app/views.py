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
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        
        # 비밀번호 변경 처리
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        password_changed = False
        
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
                messages.success(request, '프로필 정보가 성공적으로 변경되었습니다.')
        except Exception as e:
            messages.error(request, '정보 저장 중 오류가 발생했습니다.')
        
        return redirect('common_app:profile')
    
    return render(request, 'common_app/profile.html')

# 로그아웃 후 로그인 페이지로 리다이렉트하는 커스텀 뷰
def custom_logout_view(request):
    logout(request)
    return redirect('login')
