from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime, timedelta, date
from .models import FoodEvent
from common_app.models import Pet
from django.utils import timezone
from django.db.models import Q, F, ExpressionWrapper, FloatField, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import FoodEventSerializer
from item_purchase_app.models import OtherPurchase

from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@login_required
def food_calendar(request):
    pets = Pet.objects.filter(owner=request.user)
    foods = FoodEvent.objects.filter(user=request.user).order_by('-start_time')

    # 종료된 사료만 필터링
    finished_feeds = foods.filter(type='feed', end_time__isnull=False)
    avg_list = []
    for food in finished_feeds:
        days = (food.end_time.date() - food.start_time.date()).days + 1
        if days > 0 and food.quantity_kg:
            avg = food.quantity_kg / days
            avg_list.append(avg)
    overall_avg = round(sum(avg_list) / len(avg_list), 3) if avg_list else 0
    overall_avg_gram = int(overall_avg * 1000)

    today = date.today()
    total_feeds = foods.filter(type='feed').count()
    total_snacks = foods.filter(type='snack').count()
    this_month_count = foods.filter(start_time__year=today.year, start_time__month=today.month).count()
    cost_qs = FoodEvent.objects.filter(
        start_time__year=today.year,
        start_time__month=today.month
    )
    agg = cost_qs.aggregate(total=Sum('price'))
    total_cost = float(agg['total'] or 0)
    # 디버깅용: 실제 price, 날짜, 타입, 집계 포함 여부 출력 (운영시 삭제)
    print(f"[DEBUG] 현재 로그인 user id: {request.user.id}, username: {request.user.username}")
    # user 조건 없이 집계 (테스트)
    cost_qs = FoodEvent.objects.filter(
        start_time__year=today.year,
        start_time__month=today.month
    )
    agg = cost_qs.aggregate(total=Sum('price'))
    total_cost = float(agg['total'] or 0)
    # 디버깅용: 실제 price, 날짜, 타입, 집계 포함 여부 출력 (운영시 삭제)
    print(f"[DEBUG] 오늘: {today}")
    for food in foods:
        print(f"[DEBUG] id={food.id}, price={food.price}, type={food.type}, user={food.user}, start_time={food.start_time}, year={food.start_time.year}, month={food.start_time.month}")
        if food.start_time.year == today.year and food.start_time.month == today.month:
            print(f"[DEBUG]  -> 집계 포함!")
    print(f"[DEBUG] total_cost 집계 결과: {total_cost}")

    # foods에 가상 필드 추가
    for food in foods:
        food.open_date = food.start_time
        food.end_date = food.end_time
        if food.end_time:
            food.days_since_open = (food.end_time.date() - food.start_time.date()).days + 1
        else:
            food.days_since_open = (today - food.start_time.date()).days + 1

    return render(request, 'food_calendar/food_calendar.html', {
        'pets': pets,
        'foods': foods,
        'total_feeds': total_feeds,
        'total_snacks': total_snacks,
        'total_cost': total_cost,
        'overall_avg_gram': overall_avg_gram,
        'overall_avg': overall_avg,
    })

@login_required
def get_events(request, pet_id):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    # URL 쿼리에서 '+'가 space로 변환되므로 복원
    if start_str:
        start_str = start_str.replace(' ', '+')
    if end_str:
        end_str = end_str.replace(' ', '+')
    try:
        # ISO 포맷 문자열을 datetime 객체로 변환
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
    except Exception:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    end_param = end_str
    # feed(사료)는 개봉부터 종료 전까지 혹은 종료된 경우에도 윈도우 기간에 걸쳐 표시
    events = FoodEvent.objects.filter(
        user=request.user,
        pet_id=pet_id
    ).filter(
        Q(type='feed', end_time__isnull=True, start_time__lte=end_dt)
        | Q(type='feed', end_time__isnull=False, end_time__gte=start_dt, start_time__lte=end_dt)
        | Q(type='snack', start_time__gte=start_dt, start_time__lte=end_dt)
    )
    event_list = []
    for event in events:
        if event.type == 'feed':
            # 사료 이벤트: 개봉일부터 오늘 또는 종료일까지 표시하고, 섭취중이면 제목에 표시
            if event.end_time:
                end_iso = event.end_time.isoformat()
                title = f"🥣 {event.product_name} ({event.pet.name})"
            else:
                end_iso = timezone.now().isoformat()
                title = f"🥣 {event.product_name} (섭취중) ({event.pet.name})"
        elif event.type == 'snack':
            # 간식 이벤트: 개봉일에만 표시하도록 end를 start_time으로 설정
            end_iso = event.start_time.isoformat()
            title = f"🍖 {event.product_name} ({event.pet.name})"
        else:
            end_iso = event.end_time.isoformat() if event.end_time else None
            title = f"🍖 {event.product_name} ({event.pet.name})"
        event_list.append({
            'id': event.id,
            'title': title,
            'start': event.start_time.isoformat(),
            'end': end_iso,
            'pet_id': event.pet.id,
            'pet_name': event.pet.name,
            'type': event.type,
            'product_name': event.product_name,
            'purchase_link': event.purchase_link,
            'rating': event.rating,
            'previous_food': event.previous_food,
            'quantity_kg': event.quantity_kg,
            'duration_days': event.duration_days,
            'description': event.description,
        })
    return JsonResponse(event_list, safe=False)

@login_required
@require_http_methods(['POST'])
def create_event(request):
    try:
        if request.content_type.startswith('application/json'):
            data = json.loads(request.body)
        else:
            data = request.POST
        pet_id = data.get('pet_id') or data.get('pet')
        pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
        # price 값 보정
        price_val = data.get('price', 0)
        if price_val in [None, '']:
            price_val = 0
        else:
            price_val = float(price_val)
        event = FoodEvent.objects.create(
            user=request.user,
            pet=pet,
            description=data.get('description', ''),
            type=data.get('type', 'feed'),
            product_name=data.get('product_name', ''),
            purchase_link=data.get('purchase_link', ''),
            rating=data.get('rating', 0),
            previous_food=data.get('previous_food', ''),
            quantity_kg=data.get('quantity_kg', 0),
            duration_days=data.get('duration_days', 0),
            purchase_date=data.get('purchase_date') if data.get('purchase_date') else None,
            price=price_val,
            start_time=data.get('open_date') or data.get('start') or None,
            end_time=data.get('end_date') or data.get('end') or None
        )
        # 날짜 필드 보정 (FormData는 문자열로 오므로)
        if isinstance(event.purchase_date, str):
            try:
                event.purchase_date = datetime.fromisoformat(event.purchase_date).date()
            except Exception:
                event.purchase_date = None
        if isinstance(event.start_time, str):
            try:
                event.start_time = datetime.fromisoformat(event.start_time)
            except Exception:
                event.start_time = None
        if isinstance(event.end_time, str):
            try:
                event.end_time = datetime.fromisoformat(event.end_time)
            except Exception:
                event.end_time = None
        event.save()
        return JsonResponse({
            'success': True,
            'id': event.id,
            'type': event.type,
            'product_name': event.product_name,
            'purchase_link': event.purchase_link,
            'rating': event.rating,
            'previous_food': event.previous_food,
            'quantity_kg': event.quantity_kg,
            'duration_days': event.duration_days,
            'purchase_date': event.purchase_date.isoformat() if event.purchase_date else None,
            'price': str(event.price),
            'start': event.start_time.isoformat() if event.start_time else None,
            'end': event.end_time.isoformat() if event.end_time else None,
            'pet_id': event.pet.id,
            'description': event.description,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def get_event_details(request, event_id):
    event = get_object_or_404(FoodEvent, id=event_id, user=request.user)
    return JsonResponse({
        'id': event.id,
        'type': event.type,
        'product_name': event.product_name,
        'purchase_link': event.purchase_link,
        'rating': event.rating,
        'previous_food': event.previous_food,
        'quantity_kg': event.quantity_kg,
        'duration_days': event.duration_days,
        'purchase_date': event.purchase_date.isoformat() if event.purchase_date else None,
        'price': event.price,
        'start': event.start_time.isoformat() if event.start_time else None,
        'end': event.end_time.isoformat() if event.end_time else None,
        'pet_id': event.pet.id,
        'description': event.description,
    })

@login_required
@require_http_methods(['DELETE'])
def delete_event(request, event_id):
    event = get_object_or_404(FoodEvent, id=event_id, user=request.user)
    event.delete()
    return JsonResponse({'message': '이벤트가 성공적으로 삭제되었습니다.'})

@login_required
@require_http_methods(["PUT", "PATCH"])
def update_food_event(request, event_id):
    try:
        event = get_object_or_404(FoodEvent, id=event_id, user=request.user)
        data = json.loads(request.body)
        # price 값 보정
        price_val = data.get('price', 0)
        if price_val in [None, '']:
            price_val = 0
        else:
            price_val = float(price_val)
        if 'description' in data:
            event.description = data['description']
        if 'type' in data:
            event.type = data['type']
        if 'product_name' in data:
            event.product_name = data['product_name']
        if 'purchase_link' in data:
            event.purchase_link = data['purchase_link']
        if 'rating' in data:
            event.rating = data['rating']
        if 'previous_food' in data:
            event.previous_food = data['previous_food']
        if 'quantity_kg' in data:
            event.quantity_kg = data['quantity_kg']
        if 'duration_days' in data:
            event.duration_days = data['duration_days']
        if 'purchase_date' in data:
            event.purchase_date = datetime.fromisoformat(data['purchase_date']).date() if data['purchase_date'] else None
        if 'price' in data:
            event.price = price_val
        if 'end_time' in data:
            event.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        if 'pet_id' in data:
            event.pet_id = data['pet_id']
        if 'start' in data:
            if data['start']:
                dt = datetime.strptime(data['start'] + ' 12:00:00', '%Y-%m-%d %H:%M:%S')
                event.start_time = timezone.make_aware(dt)
            else:
                event.start_time = None
        event.save()
        return JsonResponse({
            'id': event.id,
            'type': event.type,
            'product_name': event.product_name,
            'purchase_link': event.purchase_link,
            'rating': event.rating,
            'previous_food': event.previous_food,
            'quantity_kg': event.quantity_kg,
            'duration_days': event.duration_days,
            'purchase_date': event.purchase_date.isoformat() if event.purchase_date else None,
            'price': event.price,
            'start_time': event.start_time.isoformat() if event.start_time else None,
            'end_time': event.end_time.isoformat() if event.end_time else None,
            'pet_id': event.pet_id,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_food_event(request, event_id):
    try:
        event = get_object_or_404(FoodEvent, id=event_id, user=request.user)
        event.delete()
        return JsonResponse({'message': '일정이 성공적으로 삭제되었습니다.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(['POST'])
def end_event(request, event_id):
    # 사료 이벤트 종료 및 통계 계산
    event = get_object_or_404(FoodEvent, id=event_id, user=request.user, type='feed')
    if event.end_time is not None:
        return JsonResponse({'error': '이미 종료된 이벤트입니다.'}, status=400)
    end_time = timezone.now()
    event.end_time = end_time
    event.save()

    # 소비 일수 및 평균 계산
    days = (event.end_time - event.start_time).days + 1
    avg_daily = event.quantity_kg / days if days > 0 else 0

    return JsonResponse({
        'id': event.id,
        'end_time': event.end_time.isoformat(),
        'days': days,
        'total_kg': event.quantity_kg,
        'avg_daily': round(avg_daily, 2),
    })

def purchase_management(request):
    # 월별 필터링
    month = request.GET.get('month')
    if month:
        year, mon = map(int, month.split('-'))
        start_date = datetime(year, mon, 1)
        if mon == 12:
            end_date = datetime(year+1, 1, 1)
        else:
            end_date = datetime(year, mon+1, 1)
    else:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
        if today.month == 12:
            end_date = datetime(today.year+1, 1, 1)
        else:
            end_date = datetime(today.year, today.month+1, 1)

    # 반려동물 필터링
    selected_pet_id = request.GET.get('pet')
    pets = Pet.objects.filter(owner=request.user)

    # 검색 필터링
    search = request.GET.get('search', '')
    
    # 일일 평균 섭취량 계산
    events = FoodEvent.objects.filter(
        user=request.user,
        purchase_date__isnull=False,
        purchase_date__gte=start_date,
        purchase_date__lt=end_date
    )
    
    if selected_pet_id:
        events = events.filter(pet_id=selected_pet_id)
    if search:
        events = events.filter(product_name__icontains=search)
    
    # 일일 평균 섭취량 계산
    events = events.annotate(
        computed_duration_days=Coalesce(
            ExpressionWrapper(
                F('end_time') - F('start_time'),
                output_field=FloatField()
            ) / (24*60*60*1000000),
            1.0
        ),
        daily_amount=ExpressionWrapper(
            F('quantity_kg') / F('computed_duration_days'),
            output_field=FloatField()
        )
    ).order_by('-purchase_date')

    # 월 총 합계(가격) 계산
    total_price = events.aggregate(
        total_price=Coalesce(
            Sum('price'),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )['total_price']
    
    selected_type = request.GET.get('type', '')
    if selected_type:
        events = events.filter(type=selected_type)
    
    # 모든 필터 적용 후에 합계 계산
    total_price = events.aggregate(
        total_price=Coalesce(
            Sum('price'),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )['total_price']

    context = {
        'events': events,
        'current_month': start_date.strftime('%Y-%m'),
        'search': search,
        'total_price': total_price,
        'pets': pets,
        'selected_pet_id': selected_pet_id,
        'selected_type': selected_type,
    }
    return render(request, 'food_calendar/purchase_management.html', context)

@login_required
def other_purchase_management(request):
    # 기타 구매 관리
    month = request.GET.get('month')
    if month:
        year, mon = map(int, month.split('-'))
        start_date = datetime(year, mon, 1)
        end_date = datetime(year if mon<12 else year+1, mon%12+1, 1)
    else:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year if today.month<12 else today.year+1, today.month%12+1, 1)
    search = request.GET.get('search', '')
    qs = OtherPurchase.objects.filter(user=request.user, purchase_date__gte=start_date, purchase_date__lt=end_date)
    if search:
        qs = qs.filter(product_name__icontains=search)
    # 총합
    total_price = qs.aggregate(total_price=Coalesce(Sum('price'), Value(0), output_field=DecimalField()))['total_price']
    context = {
        'purchases': qs.order_by('-purchase_date'),
        'current_month': start_date.strftime('%Y-%m'),
        'search': search,
        'total_price': total_price,
    }
    return render(request, 'food_calendar/other_purchase_management.html', context)

@login_required
def get_events_all(request):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    if start_str:
        start_str = start_str.replace(' ', '+')
    if end_str:
        end_str = end_str.replace(' ', '+')
    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
    except Exception:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    # 전체 반려동물의 이벤트 필터링
    events = FoodEvent.objects.filter(
        user=request.user
    ).filter(
        Q(type='feed', end_time__isnull=True, start_time__lte=end_dt)
        | Q(type='feed', end_time__isnull=False, end_time__gte=start_dt, start_time__lte=end_dt)
        | Q(type='snack', start_time__gte=start_dt, start_time__lte=end_dt)
    )
    event_list = []
    for event in events:
        if event.type == 'feed':
            if event.end_time:
                end_iso = event.end_time.isoformat()
                title = f"🥣 {event.product_name} ({event.pet.name})"
            else:
                end_iso = timezone.now().isoformat()
                title = f"🥣 {event.product_name} (섭취중) ({event.pet.name})"
        elif event.type == 'snack':
            end_iso = event.start_time.isoformat()
            title = f"🍖 {event.product_name} ({event.pet.name})"
        else:
            end_iso = event.end_time.isoformat() if event.end_time else None
            title = f"🍖 {event.product_name} ({event.pet.name})"
        event_list.append({
            'id': event.id,
            'title': title,
            'start': event.start_time.isoformat(),
            'end': end_iso,
            'pet_id': event.pet.id,
            'pet_name': event.pet.name,
            'type': event.type,
            'product_name': event.product_name,
            'purchase_link': event.purchase_link,
            'rating': event.rating,
            'previous_food': event.previous_food,
            'quantity_kg': event.quantity_kg,
            'duration_days': event.duration_days,
            'description': event.description,
        })
    return JsonResponse(event_list, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchase_management_api(request):
    month = request.GET.get('month')
    if month:
        year, mon = map(int, month.split('-'))
        start_date = datetime(year, mon, 1)
        if mon == 12:
            end_date = datetime(year+1, 1, 1)
        else:
            end_date = datetime(year, mon+1, 1)
    else:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
        if today.month == 12:
            end_date = datetime(today.year+1, 1, 1)
        else:
            end_date = datetime(today.year, today.month+1, 1)

    selected_pet_id = request.GET.get('pet')
    search = request.GET.get('search', '')
    selected_type = request.GET.get('type', '')

    events = FoodEvent.objects.filter(
        user=request.user,
        purchase_date__isnull=False,
        purchase_date__gte=start_date,
        purchase_date__lt=end_date
    )
    if selected_pet_id:
        events = events.filter(pet_id=selected_pet_id)
    if search:
        events = events.filter(product_name__icontains=search)
    if selected_type:
        events = events.filter(type=selected_type)

    # 일일 평균 섭취량 계산
    events = events.annotate(
        computed_duration_days=Coalesce(
            ExpressionWrapper(
                F('end_time') - F('start_time'),
                output_field=FloatField()
            ) / (24*60*60*1000000),
            1.0
        ),
        daily_amount=ExpressionWrapper(
            F('quantity_kg') / F('computed_duration_days'),
            output_field=FloatField()
        )
    ).order_by('-purchase_date')

    total_price = events.aggregate(
        total_price=Coalesce(
            Sum('price'),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )['total_price']

    serializer = FoodEventSerializer(events, many=True)
    return JsonResponse({
        'events': serializer.data,
        'total_price': float(total_price) if total_price is not None else 0
    })

@csrf_exempt
@login_required
@require_http_methods(['POST'])
def create_other_purchase_api(request):
    import json
    if request.content_type.startswith('application/json'):
        data = json.loads(request.body)
    else:
        data = request.POST
    purchase = OtherPurchase.objects.create(
        user=request.user,
        cat_id=data.get('pet'),
        purchase_date=data.get('purchase_date'),
        price=data.get('price', 0),
        type=data.get('type', ''),
        product_name=data.get('product_name', ''),
        purchase_link=data.get('purchase_link', ''),
        rating=data.get('rating', 0),
        memo=data.get('memo', ''),
    )
    return JsonResponse({'id': purchase.id})

@login_required
def food_stats(request):
    pet_id = request.GET.get('pet_id')
    type_param = request.GET.get('type')
    foods = FoodEvent.objects.filter(user=request.user)
    if pet_id and pet_id != 'all':
        foods = foods.filter(pet_id=pet_id)
    if type_param and type_param != 'all':
        foods = foods.filter(type=type_param)
    today = date.today()
    total_feeds = foods.filter(type='feed').count()
    total_snacks = foods.filter(type='snack').count()
    this_month_count = foods.filter(start_time__year=today.year, start_time__month=today.month).count()
    total_cost = foods.filter(purchase_date__year=today.year, purchase_date__month=today.month).aggregate(total=Sum('price'))['total'] or 0
    return JsonResponse({
        'total_feeds': total_feeds,
        'total_snacks': total_snacks,
        'this_month_count': this_month_count,
        'total_cost': int(total_cost),
    })
