from django.core.management.base import BaseCommand
from common_app.models import Pet
from insurance_app.models import PetProfile

class Command(BaseCommand):
    help = '기존 Pet 객체에 대해 PetProfile이 없으면 자동으로 생성합니다.'

    def handle(self, *args, **options):
        created_count = 0
        for pet in Pet.objects.all():
            if not PetProfile.objects.filter(user=pet.owner, name=pet.name, breed=pet.breed, birth_date=pet.birth_date).exists():
                PetProfile.objects.create(
                    user=pet.owner,
                    name=pet.name,
                    pet_type=pet.pet_type,
                    breed=pet.breed,
                    birth_date=pet.birth_date,
                    weight=pet.weight,
                    gender=getattr(pet, 'gender', 'male'),
                    is_neutered=getattr(pet, 'neutered', False),
                )
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f'PetProfile {created_count}개 생성 완료!')) 