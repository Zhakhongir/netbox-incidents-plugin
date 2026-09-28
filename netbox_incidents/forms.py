from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface, Module, Rack
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm, NetBoxModelBulkEditForm, NetBoxModelImportForm
from tenancy.models import Contact
from utilities.forms.fields import (
    CommentField, ContentTypeChoiceField, ContentTypeMultipleChoiceField, DynamicModelChoiceField,
    DynamicModelMultipleChoiceField, CSVChoiceField, CSVModelChoiceField, CSVContentTypeField,
)
from utilities.forms.rendering import FieldSet, TabbedGroups
from utilities.forms.widgets import DateTimePicker
from utilities.forms import add_blank_choice
from core.models import ObjectType

from .choices import IncidentStatusChoices, IncidentCauseChoices
from .models import Incident, ALLOWED_OBJECT_TYPES

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get('netbox_incidents', {})


def _contact_query_params():
    group_slug = PLUGIN_SETTINGS.get('contact_group_slug') or ''
    return {'group': group_slug} if group_slug else {}


class IncidentForm(NetBoxModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Устройство'),
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        selector=True,
        label=_('Интерфейс'),
    )
    module = DynamicModelChoiceField(
        queryset=Module.objects.all(),
        required=False,
        selector=True,
        label=_('Модуль'),
    )
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        selector=True,
        label=_('Стойка'),
    )
    assigned_contact = DynamicModelChoiceField(
        queryset=Contact.objects.all(),
        query_params=_contact_query_params(),
        label=_('Контактное лицо'),
        required=True,
    )
    start_date = forms.DateTimeField(
        label=_('Дата начала'),
        required=True,
        widget=DateTimePicker(),
    )
    end_date = forms.DateTimeField(
        label=_('Дата окончания'),
        required=False,
        widget=DateTimePicker(),
    )
    status = forms.ChoiceField(
        label=_('Статус'),
        choices=IncidentStatusChoices,
        required=False,
    )
    cause = forms.ChoiceField(
        label=_('Причина'),
        choices=IncidentCauseChoices,
        required=False,
    )
    comments = CommentField(
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 15,
            'class': 'font-monospace'
        }),
        label=_('Комментарий'),
    )

    fieldsets = (
        FieldSet(
            TabbedGroups(
                FieldSet('device', name=_('Устройство')),
                FieldSet('interface', name=_('Интерфейс')),
                FieldSet('module', name=_('Модуль')),
                FieldSet('rack', name=_('Стойка')),
            ),
            'assigned_contact', 'status', 'cause',
            name=_('Детали инцидента')
        ),
        FieldSet('start_date', 'end_date', name=_('Даты')),
    )

    class Meta:
        model = Incident
        fields = [
            'assigned_contact', 'start_date', 'end_date', 'status', 'cause', 'comments',
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {}).copy()

        if instance and instance.pk:
            if type(instance.assigned_object) is Device:
                initial['device'] = instance.assigned_object
            elif type(instance.assigned_object) is Interface:
                initial['interface'] = instance.assigned_object
            elif type(instance.assigned_object) is Module:
                initial['module'] = instance.assigned_object
            elif type(instance.assigned_object) is Rack:
                initial['rack'] = instance.assigned_object
            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        device = self.cleaned_data.get('device')
        interface = self.cleaned_data.get('interface')
        module = self.cleaned_data.get('module')
        rack = self.cleaned_data.get('rack')
        chosen = [x for x in (device, interface, module, rack) if x]

        if not chosen:
            raise forms.ValidationError(
                _("Выберите устройство, интерфейс, модуль или стойку.")
            )
        if len(chosen) > 1:
            raise forms.ValidationError(
                _("Инцидент можно привязать только к одному объекту.")
            )

        self.instance.assigned_object = chosen[0]

        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(
                _("Дата окончания не может быть раньше даты начала.")
            )

        return self.cleaned_data


class IncidentFilterForm(NetBoxModelFilterSetForm):
    model = Incident
    fieldsets = (
        FieldSet('q', 'filter_id'),
        FieldSet('assigned_object_type_id', 'assigned_contact', 'status', 'cause', name=_('Атрибуты')),
        FieldSet('start_date_after', 'end_date_before', name=_('Даты')),
    )
    assigned_object_type_id = ContentTypeMultipleChoiceField(
        queryset=ObjectType.objects.filter(app_label='dcim', model__in=ALLOWED_OBJECT_TYPES),
        required=False,
        label=_('Тип объекта'),
    )
    assigned_contact = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label=_('Контактное лицо'),
    )
    status = forms.ChoiceField(
        label=_('Статус'),
        choices=add_blank_choice(IncidentStatusChoices),
        required=False,
    )
    cause = forms.ChoiceField(
        label=_('Причина'),
        choices=add_blank_choice(IncidentCauseChoices),
        required=False,
    )
    start_date_after = forms.DateTimeField(
        required=False,
        label=_('Дата начала (после)'),
        widget=DateTimePicker(),
    )
    end_date_before = forms.DateTimeField(
        required=False,
        label=_('Дата окончания (до)'),
        widget=DateTimePicker(),
    )
#    tag = forms.CharField(required=False, label=_('Тег'))


class IncidentBulkEditForm(NetBoxModelBulkEditForm):
    model = Incident

    pk = forms.ModelMultipleChoiceField(
        queryset=Incident.objects.all(),
        widget=forms.MultipleHiddenInput,
    )
    status = forms.ChoiceField(
        label=_('Статус'),
        choices=add_blank_choice(IncidentStatusChoices),
        required=False,
    )
    cause = forms.ChoiceField(
        label=_('Причина'),
        choices=add_blank_choice(IncidentCauseChoices),
        required=False,
    )
    assigned_contact = DynamicModelChoiceField(
        queryset=Contact.objects.all(),
        query_params=_contact_query_params(),
        required=False,
        label=_('Контактное лицо'),
    )
    comments = CommentField(required=False)

    fieldsets = (
        FieldSet('status', 'cause', 'assigned_contact', 'comments'),
    )
    nullable_fields = ()


class IncidentImportForm(NetBoxModelImportForm):
    assigned_object_type = CSVContentTypeField(
        queryset=ObjectType.objects.filter(app_label='dcim', model__in=ALLOWED_OBJECT_TYPES),
        label=_('Тип объекта'),
    )
    assigned_contact = CSVModelChoiceField(
        queryset=Contact.objects.all(),
        to_field_name='name',
        required=False,
        label=_('Контактное лицо'),
    )
    status = CSVChoiceField(
        label=_('Статус'),
        choices=IncidentStatusChoices,
        required=False,
        help_text=_('Статус инцидента'),
    )
    cause = CSVChoiceField(
        label=_('Причина'),
        choices=IncidentCauseChoices,
        required=False,
        help_text=_('Причина инцидента'),
    )

    class Meta:
        model = Incident
        fields = (
            'assigned_object_type', 'assigned_object_id', 'assigned_contact',
            'start_date', 'end_date', 'status', 'cause', 'comments',
        )

#
# Отчёты
#

class ReportPeriodForm(forms.Form):
    date_from = forms.DateField(
        label=_('С'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    date_to = forms.DateField(
        label=_('По'),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )


REPORT_FORMS = {
    'range': ReportPeriodForm,
}

