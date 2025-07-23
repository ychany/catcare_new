from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, calendar_view, calendar_stats

router = DefaultRouter()
router.register(r'events', EventViewSet)

app_name = 'calendar_app'

urlpatterns = [
    path('', calendar_view, name='calendar'),
    path('api/', include(router.urls)),
    path('stats/', calendar_stats, name='calendar_stats'),
] 