from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Pet
from weight_tracker_app.models import Weight
import os
import json
from pathlib import Path
from datetime import date, timedelta

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class PetForm(forms.ModelForm):
    # species 필드 제거
    breed = forms.ChoiceField(
        choices=[],
        required=True,
        label='품종',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'required',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pet_type = 'cat'  # 항상 고양이로 고정
        if pet_type == 'cat':
            self.fields['breed'].choices = Pet.CAT_BREEDS
        elif pet_type == 'dog':
            self.fields['breed'].choices = Pet.DOG_BREEDS
        else:
            self.fields['breed'].choices = [('', '동물 종류를 먼저 선택해주세요')]
        # breed.json 경로 설정
        breed_path = Path(__file__).resolve().parent.parent / 'insurance_app' / 'fixtures' / 'breed.json'
        breed_choices = [('', '품종을 선택하세요')]
        if breed_path.exists():
            with open(breed_path, encoding='utf-8') as f:
                breed_data = json.load(f)
                breed_choices += [(b['fields']['name'], b['fields']['name']) for b in breed_data]
        self.fields['breed'].choices = breed_choices

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.pet_type = 'cat'  # 항상 고양이로 저장
        # 폼에서 빈 값/0이 들어오면 최근 체중 기록에서 자동 입력
        weight_val = self.cleaned_data.get('weight')
        if weight_val in [None, '', 0]:
            latest_weight = Weight.objects.filter(pet=instance).order_by('-date').first()
            if latest_weight:
                instance.weight = latest_weight.weight
            else:
                instance.weight = None
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Pet
        fields = ['name', 'breed', 'birth_date', 'gender', 'neutered', 'weight', 'notes', 'image']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        } 