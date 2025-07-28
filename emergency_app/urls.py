from django.urls import path
from . import views

app_name = 'emergency_app'

urlpatterns = [
    path('', views.hospital_list, name='hospital_list'),
    path('favorite/<int:hospital_id>/', views.toggle_favorite, name='toggle_favorite'),
] 