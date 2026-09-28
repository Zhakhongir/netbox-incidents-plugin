import django_filters
from django.utils.translation import gettext as _

from netbox.filtersets import NetBoxModelFilterSet
from tenancy.models import Contact
from utilities.filters import MultiValueContentTypeFilter

from .choices import IncidentStatusChoices, IncidentCauseChoices
from .models import Incident


class IncidentFilterSet(NetBoxModelFilterSet):
    assigned_object_type = MultiValueContentTypeFilter()
    assigned_contact_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Contact.objects.all(),
        label=_('Contact (ID)'),
    )
    assigned_contact = django_filters.ModelMultipleChoiceFilter(
        field_name='assigned_contact__name',
        queryset=Contact.objects.all(),
        to_field_name='name',
        label=_('Contact (name)'),
    )
    status = django_filters.MultipleChoiceFilter(
        choices=IncidentStatusChoices,
        label=_('Статус'),
    )
    cause = django_filters.MultipleChoiceFilter(
        choices=IncidentCauseChoices,
        label=_('Причина'),
    )
    start_date_after = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    end_date_before = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = Incident
        fields = (
            'id', 'assigned_object_type', 'assigned_object_id', 'status', 'cause',
            'assigned_contact_id', 'assigned_contact', 'start_date', 'end_date',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(comments__icontains=value)
