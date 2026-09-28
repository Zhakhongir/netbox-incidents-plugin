from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from dcim.models import Device, Interface, Module, Rack
from extras.ui.panels import CustomFieldsPanel, TagsPanel
from netbox.ui import layout
from netbox.ui.panels import CommentsPanel
from netbox.views import generic
from utilities.views import (
    ConditionalLoginRequiredMixin, ViewTab, get_action_url, get_default_template, register_model_view,
)

from . import filtersets, forms, tables
from . import reports as reports_module
from .models import Incident
from .panels import IncidentPanel

__all__ = (
    'IncidentListView',
    'IncidentView',
    'IncidentEditView',
    'IncidentDeleteView',
    'IncidentBulkImportView',
    'IncidentBulkEditView',
    'IncidentBulkDeleteView',
    'IncidentsTabView',
    'ReportsIndexView',
    'ReportGenerateView',
)

#
# Incident CRUD
#

@register_model_view(Incident, 'list', path='', detail=False)
class IncidentListView(generic.ObjectListView):
    queryset = Incident.objects.all()
    filterset = filtersets.IncidentFilterSet
    filterset_form = forms.IncidentFilterForm
    table = tables.IncidentTable


@register_model_view(Incident)
class IncidentView(generic.ObjectView):
    queryset = Incident.objects.all()
    layout = layout.SimpleLayout(
        left_panels=[
            IncidentPanel(),
            CustomFieldsPanel(),
#            TagsPanel(),
        ],
        right_panels=[
            CommentsPanel(),
        ],
    )


@register_model_view(Incident, 'add', detail=False)
@register_model_view(Incident, 'edit')
class IncidentEditView(generic.ObjectEditView):
    queryset = Incident.objects.all()
    form = forms.IncidentForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        if not obj.pk:
            obj.created_by = request.user
        return obj

    def get_return_url(self, request, instance):
        if not instance.assigned_object:
            return reverse('plugins:netbox_incidents:incident_list')
        obj = instance.assigned_object
        return get_action_url(obj, action='incidents', kwargs={'pk': obj.pk})


@register_model_view(Incident, 'delete')
class IncidentDeleteView(generic.ObjectDeleteView):
    queryset = Incident.objects.all()


@register_model_view(Incident, 'bulk_import', path='import', detail=False)
class IncidentBulkImportView(generic.BulkImportView):
    queryset = Incident.objects.all()
    model_form = forms.IncidentImportForm


@register_model_view(Incident, 'bulk_edit', path='edit', detail=False)
class IncidentBulkEditView(generic.BulkEditView):
    queryset = Incident.objects.all()
    filterset = filtersets.IncidentFilterSet
    table = tables.IncidentTable
    form = forms.IncidentBulkEditForm


@register_model_view(Incident, 'bulk_delete', path='delete', detail=False)
class IncidentBulkDeleteView(generic.BulkDeleteView):
    queryset = Incident.objects.all()
    filterset = filtersets.IncidentFilterSet
    table = tables.IncidentTable


#
# Вкладка "Incidents" на Device / Interface / Module / Rack
#

class IncidentsTabView(ConditionalLoginRequiredMixin, View):
    """
    Показывает вкладку "Incidents" на карточке объекта (Device/Interface/Module/Rack) —
    список инцидентов плюс встроенную форму добавления нового, по аналогии с
    вкладкой Journal у ядра NetBox.
    """
    base_template = None
    tab = ViewTab(
        label=_('Incidents'),
        badge=lambda obj: Incident.objects.filter(
            assigned_object_type=ContentType.objects.get_for_model(obj),
            assigned_object_id=obj.pk,
        ).count(),
        permission='netbox_incidents.view_incident',
        weight=9500,
    )

    def get(self, request, model, **kwargs):
        if hasattr(model.objects, 'restrict'):
            obj = get_object_or_404(model.objects.restrict(request.user, 'view'), **kwargs)
        else:
            obj = get_object_or_404(model, **kwargs)

        content_type = ContentType.objects.get_for_model(model)
        incidents = Incident.objects.restrict(request.user, 'view').prefetch_related(
            'created_by', 'assigned_contact'
        ).filter(
            assigned_object_type=content_type,
            assigned_object_id=obj.pk,
        )
        incident_table = tables.IncidentTable(incidents)
        incident_table.configure(request)
        incident_table.columns.hide('assigned_object_type')
        incident_table.columns.hide('assigned_object')

        _initial_key = {Device: 'device', Interface: 'interface', Module: 'module', Rack: 'rack'}.get(model)

        if request.user.has_perm('netbox_incidents.add_incident'):
            form = forms.IncidentForm(
                initial={_initial_key: obj} if _initial_key else {}
            )
        else:
            form = None

        return render(request, 'netbox_incidents/object_incidents.html', {
            'object': obj,
            'form': form,
            'table': incident_table,
            'base_template': self.base_template or get_default_template(model),
            'tab': self.tab,
        })


register_model_view(Device, 'incidents', path='incidents', kwargs={'model': Device})(IncidentsTabView)
register_model_view(Interface, 'incidents', path='incidents', kwargs={'model': Interface})(IncidentsTabView)
register_model_view(Module, 'incidents', path='incidents', kwargs={'model': Module})(IncidentsTabView)
register_model_view(Rack, 'incidents', path='incidents', kwargs={'model': Rack})(IncidentsTabView)


#
# Отчёты
#

class ReportsIndexView(ConditionalLoginRequiredMixin, View):
    """Страница со списком доступных отчётов и формами параметров для каждого."""

    def get(self, request):
        panels = []
        for report in reports_module.REPORTS:
            form_cls = forms.REPORT_FORMS[report.period_type]
            panels.append({
                'report': report,
                'form': form_cls(),
            })
        return render(request, 'netbox_incidents/reports.html', {'panels': panels})


class ReportGenerateView(ConditionalLoginRequiredMixin, View):
    """Обрабатывает запрос на генерацию конкретного отчёта."""

    def post(self, request, report_slug):
        report = reports_module.get_report(report_slug)
        if report is None:
            messages.error(request, _("Неизвестный тип отчёта."))
            return redirect('plugins:netbox_incidents:reports')

        form_cls = forms.REPORT_FORMS[report.period_type]
        form = form_cls(request.POST)

        if not form.is_valid():
            messages.error(request, _("Проверьте параметры отчёта."))
            return redirect('plugins:netbox_incidents:reports')

        if report.generator is None:
            messages.warning(
                request,
                _("Генерация отчёта «%(name)s» ещё не реализована.") % {'name': report.name}
            )
            return redirect('plugins:netbox_incidents:reports')

        return report.generator(Incident.objects.restrict(request.user, 'view'), **form.cleaned_data)
