from django.shortcuts import render
from django.http import JsonResponse
from .models import VetHospital
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
    
    return render(request, 'emergency_app/hospitals.html', {
        'hospitals': hospitals,
        'pets': pets,
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
