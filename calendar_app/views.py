from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer
from common_app.models import Pet
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from datetime import date
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Create your views here.

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(pet__owner=self.request.user)

    def perform_create(self, serializer):
        # 고양이 소유자 확인
        pet = Pet.objects.get(id=self.request.data.get('pet'))
        if pet.owner != self.request.user:
            raise permissions.PermissionDenied("You don't have permission to create events for this pet.")
        serializer.save()

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@ensure_csrf_cookie
@login_required
def calendar_view(request):
    pets = Pet.objects.filter(owner=request.user)
    next_vacc_list = []
    today = date.today()
    events = Event.objects.filter(pet__owner=request.user)

    total_medical = events.filter(event_type='med').count()
    total_vaccination = events.filter(event_type='vacc').count()
    upcoming_vacc = events.filter(event_type='vacc', next_date__gte=today).count()
    total_cost = events.filter(date__year=today.year, date__month=today.month).aggregate(total=Sum('cost'))['total'] or 0

    for pet in pets:
        # 미래의 모든 next_date
        next_vaccs = Event.objects.filter(
            pet=pet, event_type='vacc', next_date__isnull=False, next_date__gte=today
        ).order_by('next_date')
        for next_vacc in next_vaccs:
            days_left = (next_vacc.next_date - today).days
            next_vacc_list.append({
                'pet_name': pet.name,
                'next_date': next_vacc.next_date,
                'days_left': days_left
            })
    # 기존 last_events도 유지
    last_events = []
    for pet in pets:
        event = Event.objects.filter(pet=pet).order_by('-date').first()
        if event:
            last_events.append({
                'pet_id': pet.id,
                'date': event.date,
                'event_type': event.get_event_type_display(),
                'description': event.description
            })
    medical_records = events.order_by('-date')
    return render(request, 'calendar_app/calendar.html', {
        'pets': pets,
        'last_events': last_events,
        'next_vacc_list': next_vacc_list,
        'medical_records': medical_records,
        'total_medical': total_medical,
        'total_vaccination': total_vaccination,
        'upcoming_vacc': upcoming_vacc,
        'total_cost': total_cost,
    })

@require_GET
@login_required
def calendar_stats(request):
    pet_id = request.GET.get('pet_id')
    today = date.today()
    events = Event.objects.filter(pet__owner=request.user)
    if pet_id and pet_id != 'all':
        events = events.filter(pet_id=pet_id)
    total_medical = events.filter(event_type='med').count()
    total_vaccination = events.filter(event_type='vacc').count()
    upcoming_vacc = events.filter(event_type='vacc', next_date__gte=today).count()
    total_cost = events.filter(date__year=today.year, date__month=today.month).aggregate(total=Sum('cost'))['total'] or 0
    return JsonResponse({
        'total_medical': total_medical,
        'total_vaccination': total_vaccination,
        'upcoming_vacc': upcoming_vacc,
        'total_cost': total_cost,
    })
