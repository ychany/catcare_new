from django.urls import path
from . import views

app_name = 'food_calendar'

urlpatterns = [
    path('', views.food_calendar, name='food_calendar'),
    path('events/', views.get_events_all, name='get_events_all'),
    path('events/<int:pet_id>/', views.get_events, name='get_events'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/<int:event_id>/', views.get_event_details, name='get_event_details'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('event/<int:event_id>/update/', views.update_food_event, name='update_event'),
    path('event/<int:event_id>/end/', views.end_event, name='end_event'),
    path('purchases/', views.purchase_management, name='purchase_management'),
    path('api/purchases/management/', views.purchase_management_api, name='purchase_management_api'),
    path('api/purchases/other/', views.create_other_purchase_api, name='create_other_purchase_api'),
] 