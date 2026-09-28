from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from netbox.api.fields import ChoiceField, ContentTypeField
from netbox.api.serializers import NetBoxModelSerializer
from tenancy.api.serializers import ContactSerializer
from users.api.serializers import UserSerializer
from utilities.api import get_serializer_for_model

from ..choices import IncidentCauseChoices, IncidentStatusChoices
from ..models import ALLOWED_OBJECT_TYPES, Incident


class IncidentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_incidents-api:incident-detail'
    )
    assigned_object_type = ContentTypeField(
        queryset=ContentType.objects.filter(app_label='dcim', model__in=ALLOWED_OBJECT_TYPES),
    )
    assigned_object = serializers.SerializerMethodField(read_only=True)
    assigned_contact = ContactSerializer(nested=True, required=False, allow_null=True)
    created_by = UserSerializer(nested=True, required=False, allow_null=True, read_only=True)
    status = ChoiceField(choices=IncidentStatusChoices, required=False)
    cause = ChoiceField(choices=IncidentCauseChoices, required=False)

    class Meta:
        model = Incident
        fields = (
            'id', 'url', 'display', 'assigned_object_type', 'assigned_object_id', 'assigned_object',
            'assigned_contact', 'start_date', 'end_date', 'status', 'cause', 'comments',
            'created_by', 'tags', 'custom_fields', 'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'status', 'cause', 'start_date', 'end_date')

    def get_assigned_object(self, obj):
        if obj.assigned_object is None:
            return None
        serializer = get_serializer_for_model(obj.assigned_object)
        context = {'request': self.context.get('request')}
        return serializer(obj.assigned_object, nested=True, context=context).data
