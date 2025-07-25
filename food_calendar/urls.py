from django.urls import path
from .views import food_calendar, get_events, create_event, get_event_details, delete_event, update_food_event, end_event, purchase_management, other_purchase_management, get_events_all, food_stats

app_name = 'food_calendar'

urlpatterns = [
    path('', food_calendar, name='food_calendar'),
    path('event/<int:pet_id>/', get_events, name='get_events'),
    path('event/create/', create_event, name='create_event'),
    path('event/<int:event_id>/', get_event_details, name='get_event_details'),
    path('event/<int:event_id>/delete/', delete_event, name='delete_event'),
    path('event/<int:event_id>/update/', update_food_event, name='update_food_event'),
    path('event/<int:event_id>/end/', end_event, name='end_event'),
    path('purchase/', purchase_management, name='purchase_management'),
    path('other_purchase/', other_purchase_management, name='other_purchase_management'),
    path('events/all/', get_events_all, name='get_events_all'),
    path('stats/', food_stats, name='food_stats'),
] 