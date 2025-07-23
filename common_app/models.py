from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Pet(models.Model):
    PET_TYPE_CHOICES = [
        ('dog', '강아지'),
        ('cat', '고양이'),
    ]

    CAT_BREEDS = [
        ('persian', '페르시안'),
        ('siamese', '샴'),
        ('maine_coon', '메인쿤'),
        ('ragdoll', '랙돌'),
        ('british', '브리티시 숏헤어'),
        ('scottish', '스코티시 폴드'),
        ('russian', '러시안 블루'),
        ('abyssinian', '아비시니안'),
        ('bengal', '벵갈'),
        ('sphynx', '스핑크스'),
        ('etc', '기타'),
    ]

    DOG_BREEDS = [
        ('poodle', '푸들'),
        ('chihuahua', '치와와'),
        ('shih_tzu', '시츄'),
        ('maltese', '말티즈'),
        ('pomeranian', '포메라니안'),
        ('yorkshire', '요크셔테리어'),
        ('dachshund', '닥스훈트'),
        ('beagle', '비글'),
        ('golden_retriever', '골든 리트리버'),
        ('labrador', '래브라도 리트리버'),
        ('etc', '기타'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100, verbose_name='이름')
    pet_type = models.CharField(max_length=10, choices=PET_TYPE_CHOICES, verbose_name='종류', default='cat')
    breed = models.CharField(max_length=20, verbose_name='품종')
    birth_date = models.DateField(verbose_name='생년월일')
    weight = models.FloatField(verbose_name='체중(kg)', null=True, blank=True)
    image = models.ImageField(upload_to='pet_images/', verbose_name='프로필 사진', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    gender = models.CharField(max_length=10, choices=[('male', '수컷'), ('female', '암컷')], verbose_name='성별', default='male')
    neutered = models.BooleanField(verbose_name='중성화 여부', default=False)
    notes = models.TextField(verbose_name='특이사항', blank=True)
    preference_dict = models.JSONField(verbose_name='보험 선호도', default=dict, blank=True)

    class Meta:
        verbose_name = '반려동물'
        verbose_name_plural = '반려동물들'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_pet_type_display()})"

    def get_age(self):
        """나이 계산"""
        today = date.today()
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month or (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        return age

    def days_until_birthday(self):
        today = date.today()
        next_birthday = date(today.year, self.birth_date.month, self.birth_date.day)
        if next_birthday < today:
            next_birthday = date(today.year + 1, self.birth_date.month, self.birth_date.day)
        return (next_birthday - today).days

    def birthday_progress(self):
        """생일까지 남은 날짜의 진행률을 계산합니다."""
        days_until = self.days_until_birthday()
        # 1년을 100%로 보고 남은 날짜의 비율을 계산
        progress = ((365 - days_until) / 365) * 100
        return round(progress, 1)

    def get_breed_choices(self):
        """펫 타입에 따른 품종 선택지 반환"""
        if self.pet_type == 'dog':
            return self.DOG_BREEDS
        elif self.pet_type == 'cat':
            return self.CAT_BREEDS
        return []

    def get_breed_display_custom(self):
        """품종 한글명 반환"""
        breed_choices = self.get_breed_choices()
        for choice_value, choice_label in breed_choices:
            if self.breed == choice_value:
                return choice_label
        return self.breed
