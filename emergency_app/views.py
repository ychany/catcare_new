from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import VetHospital, HospitalFavorite
import json
from common_app.models import Pet
from django.db import models

# Create your views here.

def hospital_list(request):
    # 검색 파라미터 처리
    search_query = request.GET.get('search', '')
    hospital_type = request.GET.get('type', 'all')
    
    # 기본 병원 리스트 
    hospitals = VetHospital.objects.all()
    
    # 검색 필터링
    if search_query:
        hospitals = hospitals.filter(
            models.Q(name__icontains=search_query) |
            models.Q(address__icontains=search_query)
        )
    
    # 타입 필터링
    if hospital_type == 'emergency':
        hospitals = hospitals.filter(is_emergency=True)
    elif hospital_type == '24hours':
        hospitals = hospitals.filter(is_24hours=True)
    
    # 샘플 데이터가 없을 경우 기본 데이터 생성
    if not hospitals.exists():
        create_sample_hospitals()
        hospitals = VetHospital.objects.all()
    
    # 로그인한 유저의 펫 정보
    pets = Pet.objects.filter(owner=request.user) if request.user.is_authenticated else []
    
    # 로그인한 유저의 즐겨찾기 병원 목록
    favorite_hospitals = []
    favorite_hospital_ids = []
    if request.user.is_authenticated:
        favorite_hospitals = HospitalFavorite.objects.filter(user=request.user).select_related('hospital')
        favorite_hospital_ids = list(favorite_hospitals.values_list('hospital_id', flat=True))
    
    return render(request, 'emergency_app/hospitals.html', {
        'hospitals': hospitals,
        'pets': pets,
        'favorite_hospitals': favorite_hospitals,
        'favorite_hospital_ids': favorite_hospital_ids,
        'search_query': search_query,
        'hospital_type': hospital_type,
    })

def create_sample_hospitals():
    """샘플 병원 데이터 생성"""
    hospitals_data = [
        {
            'name': '24시 우리동물병원',
            'address': '서울특별시 강남구 테헤란로 123',
            'phone': '02-1234-5678',
            'is_24hours': True,
            'is_emergency': True,
            'rating': 4.8,
            'distance_km': 0.5,
            'operating_hours': '24시간 운영',
            'specialties': '내과,외과,응급처치',
            'latitude': 37.5665,
            'longitude': 126.9780,
        },
        {
            'name': '사랑동물병원',
            'address': '서울특별시 강남구 역삼로 456',
            'phone': '02-2345-6789',
            'is_24hours': False,
            'is_emergency': False,
            'rating': 4.5,
            'distance_km': 1.2,
            'operating_hours': '09:00 - 18:00',
            'specialties': '일반진료,예방접종,건강검진',
            'latitude': 37.5635,
            'longitude': 126.9800,
        },
        {
            'name': '고양이 전문병원',
            'address': '서울특별시 서초구 강남대로 789',
            'phone': '02-3456-7890',
            'is_24hours': False,
            'is_emergency': False,
            'rating': 4.7,
            'distance_km': 2.1,
            'operating_hours': '10:00 - 20:00',
            'specialties': '고양이 전문,행동치료,피부과',
            'latitude': 37.5605,
            'longitude': 126.9820,
        },
        {
            'name': '응급동물병원',
            'address': '서울특별시 강남구 논현로 321',
            'phone': '02-4567-8901',
            'is_24hours': True,
            'is_emergency': True,
            'rating': 4.3,
            'distance_km': 1.8,
            'operating_hours': '24시간 응급실',
            'specialties': '응급처치,중환자실,수술',
            'latitude': 37.5645,
            'longitude': 126.9760,
        }
    ]
    
    for data in hospitals_data:
        VetHospital.objects.get_or_create(
            name=data['name'],
            defaults=data
        )

@login_required
def add_search_hospital(request):
    """검색된 병원을 DB에 추가하고 즐겨찾기에 추가"""
    print("=== DEBUG: add_search_hospital view called ===")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"Request POST data: {request.POST}")
    print(f"Request user: {request.user}")
    print(f"User authenticated: {request.user.is_authenticated}")
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            address = request.POST.get('address') 
            phone = request.POST.get('phone', '정보 없음')
            lat = float(request.POST.get('lat', 0))
            lng = float(request.POST.get('lng', 0))
            
            if not name or not address:
                return JsonResponse({'error': '병원명과 주소는 필수입니다.'}, status=400)
            
            # 이미 존재하는 병원인지 확인 (이름과 주소로)
            hospital, created = VetHospital.objects.get_or_create(
                name=name,
                address=address,
                defaults={
                    'phone': phone,
                    'latitude': lat,
                    'longitude': lng,
                    'is_24hours': False,
                    'is_emergency': False,
                    'rating': 0.0,
                    'distance_km': 0.0,
                    'operating_hours': '정보 없음',
                    'specialties': '',
                    'description': '검색을 통해 추가된 병원'
                }
            )
            
            # 즐겨찾기 추가
            favorite, fav_created = HospitalFavorite.objects.get_or_create(
                user=request.user,
                hospital=hospital
            )
            
            return JsonResponse({
                'success': True,
                'hospital_id': hospital.id,
                'is_favorite': True,
                'message': '병원이 즐겨찾기에 추가되었습니다.'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

def debug_urls(request):
    """URL 디버깅용 뷰"""
    from django.urls import reverse
    from django.conf import settings
    import sys
    try:
        url_info = {
            'current_path': request.path,
            'method': request.method,
            'user': str(request.user),
            'authenticated': request.user.is_authenticated,
            'root_urlconf': settings.ROOT_URLCONF,
            'django_settings_module': getattr(settings, 'DJANGO_SETTINGS_MODULE', 'Not set'),
            'python_path': sys.path[:3],  # 처음 3개 경로만
        }
        
        # URL reverse 테스트
        try:
            url_info['emergency_urls'] = {
                'hospital_list': reverse('emergency_app:hospital_list'),
                'add_search_hospital': reverse('emergency_app:add_search_hospital'),
            }
        except Exception as e:
            url_info['emergency_urls_error'] = str(e)
            
        return JsonResponse(url_info)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def toggle_favorite(request, hospital_id):
    """병원 즐겨찾기 토글"""
    if request.method == 'POST':
        # 검색된 병원 추가 요청인지 확인 (특별한 필드가 있는지)
        if 'name' in request.POST and 'address' in request.POST:
            try:
                name = request.POST.get('name')
                address = request.POST.get('address') 
                phone = request.POST.get('phone', '정보 없음')
                lat = float(request.POST.get('lat', 0))
                lng = float(request.POST.get('lng', 0))
                
                if not name or not address:
                    return JsonResponse({'error': '병원명과 주소는 필수입니다.'}, status=400)
                
                # 이미 존재하는 병원인지 확인 (이름과 주소로)
                hospital, created = VetHospital.objects.get_or_create(
                    name=name,
                    address=address,
                    defaults={
                        'phone': phone,
                        'latitude': lat,
                        'longitude': lng,
                        'is_24hours': False,
                        'is_emergency': False,
                        'rating': 0.0,
                        'distance_km': 0.0,
                        'operating_hours': '정보 없음',
                        'specialties': '',
                        'description': '검색을 통해 추가된 병원'
                    }
                )
                
                # 즐겨찾기 추가
                favorite, fav_created = HospitalFavorite.objects.get_or_create(
                    user=request.user,
                    hospital=hospital
                )
                
                return JsonResponse({
                    'success': True,
                    'hospital_id': hospital.id,
                    'is_favorite': True,
                    'message': '병원이 즐겨찾기에 추가되었습니다.'
                })
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        else:
            # 일반 즐겨찾기 토글
            hospital = get_object_or_404(VetHospital, id=hospital_id)
            favorite, created = HospitalFavorite.objects.get_or_create(
                user=request.user,
                hospital=hospital
            )
            
            if not created:
                favorite.delete()
                is_favorite = False
            else:
                is_favorite = True
            
            return JsonResponse({
                'is_favorite': is_favorite,
                'message': '즐겨찾기에 추가되었습니다.' if is_favorite else '즐겨찾기에서 제거되었습니다.'
            })


