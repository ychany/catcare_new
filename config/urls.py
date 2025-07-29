from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from common_app import views as common_views
from common_app.views import kakao_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    # 루트 URL을 로그인 페이지로 직접 리다이렉트
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='root_redirect'),
    # 기존 홈페이지 URL (common_app을 사용)
    path('home/', include('common_app.urls')),
    path('board/', include('photo_board_app.urls')),
    path('calendar/', include(('calendar_app.urls', 'calendar_app'), namespace='calendar_app')),
    path('care/', include('care_calendar.urls', namespace='care_calendar')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='common_app/login.html'), name='login'),
    path('accounts/logout/', common_views.custom_logout_view, name='logout'),
    path('register/', common_views.register, name='register'),
    path('index/', common_views.index, name='index'),
    path('kakao/callback/', kakao_callback, name='kakao_callback'),
    path('weight/', include(('weight_tracker_app.urls', 'weight_tracker_app'), namespace='weight_tracker_app')),
    path('insurance/', include('insurance_app.urls', namespace='insurance')),
    path('items/', include('item_purchase_app.urls')),
    path('food/', include('food_calendar.urls')),
    path('community/', include('community_app.urls', namespace='community_app')),
    path('emergency/', include('emergency_app.urls', namespace='emergency_app')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 