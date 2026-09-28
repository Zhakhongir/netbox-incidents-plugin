import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns
from .models import Incident


class IncidentTable(NetBoxTable):
    status = columns.ChoiceFieldColumn(
        verbose_name=_('Статус'),
    )
    cause = columns.ChoiceFieldColumn(
        verbose_name=_('Причина'),
    )
    assigned_object_type = columns.ContentTypeColumn(
        verbose_name=_('Тип объекта'),
    )
    assigned_object = tables.Column(
        linkify=True,
        orderable=False,
        verbose_name=_('Объект'),
    )
    assigned_contact = tables.Column(
        linkify=True,
        verbose_name=_('Контакт'),
    )
    start_date = columns.DateTimeColumn(
        timespec='minutes',
        verbose_name=_('Дата начала'),
    )
    end_date = columns.DateTimeColumn(
        timespec='minutes',
        verbose_name=_('Дата окончания'),
    )
    comments = columns.MarkdownColumn(
        verbose_name=_('Комментарий'),
    )
    comments_short = tables.TemplateColumn(
        accessor=tables.A('comments'),
        template_code='{{ value|markdown|truncatewords_html:50 }}',
        verbose_name=_('Комментарий (кратко)'),
    )
#    tags = columns.TagColumn(
#        url_name='plugins:netbox_incidents:incident_list'
#    )

    class Meta(NetBoxTable.Meta):
        model = Incident
        fields = (
            'pk', 'id', 'status', 'cause', 'assigned_object_type', 'assigned_object', 'assigned_contact',
            'start_date', 'end_date', 'comments', 'comments_short', 'created_by',
            'created', 'last_updated', 'actions',
        )
        default_columns = (
            'pk', 'status', 'cause', 'start_date', 'end_date', 'assigned_object', 'assigned_contact',
            'comments_short',
        )
