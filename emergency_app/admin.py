from django.contrib import admin
from .models import VetHospital

@admin.register(VetHospital)
class VetHospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'rating', 'distance_km', 'is_24hours', 'is_emergency']
    list_filter = ['is_24hours', 'is_emergency', 'rating']
    search_fields = ['name', 'address', 'phone']
    list_editable = ['rating', 'distance_km', 'is_24hours', 'is_emergency']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'address', 'phone', 'image')
        }),
        ('운영 정보', {
            'fields': ('operating_hours', 'is_24hours', 'is_emergency')
        }),
        ('평가 정보', {
            'fields': ('rating', 'distance_km')
        }),
        ('상세 정보', {
            'fields': ('specialties', 'description')
        }),
        ('위치 정보', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
    )
    
    def get_specialties_display(self, obj):
        return ', '.join(obj.get_specialties_list())
    get_specialties_display.short_description = '전문분야'
