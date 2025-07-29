from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime, timedelta
from .models import OtherPurchase
from common_app.models import Pet
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .serializers import OtherPurchaseSerializer
from django.db.models import Sum, Value, DecimalField, Count
from django.db.models.functions import Coalesce

# Create your views here.

@login_required
@require_http_methods(['GET'])
def other_purchase_management(request):
    # 기타 구매 관리 뷰
    # 날짜/월별 필터링
    month = request.GET.get('month')
    if month:
        if len(month) == 10:  # YYYY-MM-DD 형식
            selected_date = datetime.strptime(month, '%Y-%m-%d')
            start_date = datetime(selected_date.year, selected_date.month, 1)
            end_date = datetime(selected_date.year if selected_date.month<12 else selected_date.year+1, selected_date.month%12+1, 1)
        elif len(month) == 7:  # YYYY-MM 형식
            year, mon = map(int, month.split('-'))
            start_date = datetime(year, mon, 1)
            end_date = datetime(year if mon<12 else year+1, mon%12+1, 1)
        else:
            today = datetime.now()
            start_date = datetime(today.year, today.month, 1)
            end_date = datetime(today.year if today.month<12 else today.year+1, today.month%12+1, 1)
    else:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year if today.month<12 else today.year+1, today.month%12+1, 1)
    
    # 반려동물 필터링
    selected_pet_id = request.GET.get('pet')
    pets = Pet.objects.filter(owner=request.user)
    
    # 검색 및 카테고리 필터링
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    qs = OtherPurchase.objects.filter(user=request.user, purchase_date__gte=start_date, purchase_date__lt=end_date)
    
    if selected_pet_id:
        qs = qs.filter(cat_id=selected_pet_id)
    if search:
        qs = qs.filter(product_name__icontains=search)
    if category:
        qs = qs.filter(type=category)
    
    # 총 합계
    total_price = qs.aggregate(total_price=Coalesce(Sum('price'), Value(0), output_field=DecimalField()))['total_price']
    
    # 지난달 데이터 계산
    last_month_start = start_date - timedelta(days=30)
    last_month_end = start_date
    last_month_qs = OtherPurchase.objects.filter(user=request.user, purchase_date__gte=last_month_start, purchase_date__lt=last_month_end)
    if selected_pet_id:
        last_month_qs = last_month_qs.filter(cat_id=selected_pet_id)
    last_month_total = last_month_qs.aggregate(total_price=Coalesce(Sum('price'), Value(0), output_field=DecimalField()))['total_price']
    
    # 지난달 대비 변화율 계산
    if last_month_total and last_month_total > 0:
        change_percentage = ((total_price - last_month_total) / last_month_total) * 100
        if change_percentage > 0:
            trend_text = f"지난달 대비 +{change_percentage:.1f}%"
            trend_icon = "fas fa-arrow-up"
        elif change_percentage < 0:
            trend_text = f"지난달 대비 {change_percentage:.1f}%"
            trend_icon = "fas fa-arrow-down"
        else:
            trend_text = "지난달과 동일"
            trend_icon = "fas fa-minus"
    else:
        trend_text = "지난달 데이터 없음"
        trend_icon = "fas fa-minus"
    
    # 평소와의 비교 (최근 3개월 평균 대비)
    three_months_ago = start_date - timedelta(days=90)
    three_months_qs = OtherPurchase.objects.filter(user=request.user, purchase_date__gte=three_months_ago, purchase_date__lt=start_date)
    if selected_pet_id:
        three_months_qs = three_months_qs.filter(cat_id=selected_pet_id)
    three_months_total = three_months_qs.aggregate(total_price=Coalesce(Sum('price'), Value(0), output_field=DecimalField()))['total_price']
    
    if three_months_total and three_months_total > 0:
        avg_monthly = three_months_total / 3
        current_vs_avg = ((total_price - avg_monthly) / avg_monthly) * 100
        if abs(current_vs_avg) < 10:  # 10% 이내면 평소와 비슷
            daily_trend_text = "평소와 비슷"
            daily_trend_icon = "fas fa-minus"
        elif current_vs_avg > 10:
            daily_trend_text = f"평소 대비 +{current_vs_avg:.1f}%"
            daily_trend_icon = "fas fa-arrow-up"
        else:
            daily_trend_text = f"평소 대비 {current_vs_avg:.1f}%"
            daily_trend_icon = "fas fa-arrow-down"
    else:
        daily_trend_text = "평소 데이터 없음"
        daily_trend_icon = "fas fa-minus"
    
    # 구매 건수 변화
    current_count = qs.count()
    last_month_count = last_month_qs.count()
    if last_month_count > 0:
        count_change = current_count - last_month_count
        if count_change > 0:
            count_trend_text = f"+{count_change}건"
            count_trend_icon = "fas fa-arrow-up"
        elif count_change < 0:
            count_trend_text = f"{count_change}건"
            count_trend_icon = "fas fa-arrow-down"
        else:
            count_trend_text = "변화없음"
            count_trend_icon = "fas fa-minus"
    else:
        count_trend_text = "지난달 데이터 없음"
        count_trend_icon = "fas fa-minus"
    
    category_labels = ['장난감', '간식', '용품', '의료', '미용', '기타']
    category_totals = []
    for label in category_labels:
        total = qs.filter(type=label).aggregate(sum=Sum('price'))['sum'] or 0
        category_totals.append(int(total))
    
    # 일 평균 지출
    days = (end_date - start_date).days or 1
    average_daily = int(total_price // days) if total_price else 0
    # 최대 지출
    largest = qs.order_by('-price').first()
    largest_expense = largest.price if largest else 0
    largest_category = largest.type if largest else ''
    # 선택된 월 설정 (파라미터로 전달된 월 또는 현재 월)
    if month:
        if len(month) == 10:  # YYYY-MM-DD 형식으로 전달된 경우
            selected_month_str = month[:7]  # YYYY-MM 형식으로 변환
        elif len(month) == 7:  # YYYY-MM 형식
            selected_month_str = month
        else:
            selected_month_str = datetime.now().strftime('%Y-%m')
    else:
        selected_month_str = datetime.now().strftime('%Y-%m')
    
    context = {
        'purchases': qs.order_by('-purchase_date'),
        'current_month': selected_month_str,
        'search': search,
        'selected_category': category,
        'total_price': total_price,
        'pets': pets,
        'selected_pet_id': selected_pet_id,
        'trend_text': trend_text,
        'trend_icon': trend_icon,
        'daily_trend_text': daily_trend_text,
        'daily_trend_icon': daily_trend_icon,
        'count_trend_text': count_trend_text,
        'count_trend_icon': count_trend_icon,
    }
    context.update({
        'category_labels': category_labels,
        'category_totals': category_totals,
        'average_daily': average_daily,
        'largest_expense': largest_expense,
        'largest_category': largest_category,
    })
    return render(request, 'item_purchase_app/other_purchase_management.html', context)

@login_required
@require_http_methods(['POST'])
def create_other_purchase(request):
    try:
        data = json.loads(request.body)
        default_cat = Pet.objects.filter(owner=request.user).first()
        purchase = OtherPurchase.objects.create(
            user=request.user,
            cat=default_cat,
            purchase_date=datetime.fromisoformat(data['purchase_date']),
            price=int(data.get('price', 0)),
            type=data.get('type', ''),
            product_name=data.get('product_name', ''),
            purchase_link=data.get('purchase_link', ''),
            rating=int(data.get('rating', 0)),
            memo=data.get('memo', ''),
        )
        return JsonResponse({'id': purchase.id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

class OtherPurchaseViewSet(ModelViewSet):
    queryset = OtherPurchase.objects.all().order_by('-purchase_date')
    serializer_class = OtherPurchaseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().filter(user=self.request.user)
        month = self.request.query_params.get('month')
        if month:
            y, m = map(int, month.split('-'))
            qs = qs.filter(purchase_date__year=y, purchase_date__month=m)
        pet = self.request.query_params.get('pet')
        if pet:
            qs = qs.filter(cat_id=pet)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(product_name__icontains=search)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        total_price = queryset.aggregate(total_price=Coalesce(Sum('price'), Value(0), output_field=DecimalField()))['total_price']
        return JsonResponse({
            'purchases': serializer.data,
            'total_price': int(total_price) if total_price is not None else 0
        }, safe=False)

    def perform_create(self, serializer):
        pet_id = self.request.data.get('pet')
        if pet_id:
            pet = get_object_or_404(Pet, id=pet_id, owner=self.request.user)
        else:
            pet = Pet.objects.filter(owner=self.request.user).first()
        serializer.save(user=self.request.user, cat=pet)
