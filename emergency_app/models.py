from django.db import models

# Create your models here.

class VetHospital(models.Model):
    name = models.CharField(max_length=100, verbose_name='병원명')
    address = models.CharField(max_length=200, verbose_name='주소')
    phone = models.CharField(max_length=20, verbose_name='전화번호')
    is_24hours = models.BooleanField(default=False, verbose_name='24시간 운영')
    latitude = models.FloatField(verbose_name='위도')
    longitude = models.FloatField(verbose_name='경도')
    
    # 추가 필드들
    image = models.ImageField(upload_to='hospitals/', blank=True, null=True, verbose_name='병원 이미지')
    rating = models.FloatField(default=0.0, verbose_name='별점')
    distance_km = models.FloatField(default=0.0, verbose_name='거리(km)')
    operating_hours = models.CharField(max_length=100, default='09:00 - 18:00', verbose_name='운영시간')
    specialties = models.TextField(blank=True, verbose_name='전문분야 (쉼표로 구분)')
    is_emergency = models.BooleanField(default=False, verbose_name='응급실 운영')
    description = models.TextField(blank=True, verbose_name='병원 설명')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    def __str__(self):
        return self.name

    def get_specialties_list(self):
        return [s.strip() for s in self.specialties.split(',') if s.strip()]

    class Meta:
        verbose_name = '동물병원'
        verbose_name_plural = '동물병원 목록'
        ordering = ['-rating', 'distance_km']
