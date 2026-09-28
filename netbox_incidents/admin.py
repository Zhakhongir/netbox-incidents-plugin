from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'cause', 'assigned_object_type', 'assigned_object_id', 'assigned_contact', 'start_date', 'end_date')
    list_filter = ('status', 'cause', 'assigned_object_type')
