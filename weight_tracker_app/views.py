from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError
from .models import Weight
from .serializers import WeightSerializer
from django.db.models import Avg
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone
from common_app.models import Pet
import json
from collections import defaultdict

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def weight_list(request):
    if request.method == 'GET':
        pet_id = request.GET.get('pet_id')
        weights = Weight.objects.filter(user=request.user)
        if pet_id:
            weights = weights.filter(pet_id=pet_id)
        weights = weights.order_by('-pet_id', '-date')
        data = []
        pet_weights = defaultdict(list)
        for weight in weights:
            pet_weights[weight.pet_id].append(weight)
        for pet_id, weight_list in pet_weights.items():
            for i, weight in enumerate(weight_list):
                weight_data = {
                    'id': weight.id,
                    'pet': weight.pet_id,
                    'pet_name': weight.pet.name if weight.pet else '',
                    'date': weight.date,
                    'weight': float(weight.weight),
                    'change': None,
                    'days_since_last': None
                }
                if i < len(weight_list) - 1:
                    prev_weight = weight_list[i + 1]
                    weight_data['change'] = float(weight.weight) - float(prev_weight.weight)
                    weight_data['days_since_last'] = (weight.date - prev_weight.date).days
                data.append(weight_data)
        data.sort(key=lambda x: (x['pet'], x['date']), reverse=True)
        return Response(data)
    
    elif request.method == 'POST':
        serializer = WeightSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({
                    'error': '이미 해당 날짜에 이 반려동물의 체중 기록이 존재합니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def weight_delete(request, pk):
    try:
        weight = Weight.objects.get(pk=pk, user=request.user)
        weight.delete()
        return Response({'status': 'success'})
    except Weight.DoesNotExist:
        return Response({'status': 'error', 'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

def weight_tracker_view(request):
    user_pets = list(Pet.objects.filter(owner=request.user).values('id', 'name')) if request.user.is_authenticated else []
    return render(request, 'weight_tracker/index.html', {'user_pets': json.dumps(user_pets)})
