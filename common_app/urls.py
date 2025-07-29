from django.urls import path
from . import views

app_name = 'common_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<int:pet_id>/', views.pet_edit, name='pet_edit'),
    path('update/<int:pet_id>/', views.pet_update, name='pet_update'),
    path('register/', views.pet_register, name='pet_register'),
    path('delete/<int:pet_id>/', views.pet_delete, name='pet_delete'),
    path('profile/', views.profile, name='profile'),
] 