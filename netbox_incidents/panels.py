from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels


class IncidentPanel(panels.ObjectAttributesPanel):
    title = _('Инцидент')

    assigned_object = attrs.GenericForeignKeyAttr('assigned_object', linkify=True, label=_('Объект'))
    assigned_contact = attrs.RelatedObjectAttr('assigned_contact', linkify=True, label=_('Контактное лицо'))
    status = attrs.ChoiceAttr('status', label=_('Статус'))
    cause = attrs.ChoiceAttr('cause', label=_('Причина'))
    start_date = attrs.DateTimeAttr('start_date', spec='minutes', label=_('Дата начала'))
    end_date = attrs.DateTimeAttr('end_date', spec='minutes', label=_('Дата окончания'))
    created_by = attrs.TextAttr('created_by', label=_('Создано пользователем'))
