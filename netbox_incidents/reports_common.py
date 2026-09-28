"""Общие хелперы сбора данных для генераторов отчётов netbox_incidents."""
import datetime as dt
from dataclasses import dataclass
from typing import Optional

from django.db.models import Q

from dcim.models import Device, Interface, Module, Rack

OBJECT_TYPE_LABELS = {
    'rack': 'Стойка',
    'device': 'Устройство',
    'module': 'Модуль',
    'interface': 'Интерфейс',
}
OBJECT_TYPE_ORDER = ['rack', 'device', 'module', 'interface']


@dataclass
class ResolvedIncident:
    incident_id: int
    object_type: str             # 'rack' | 'device' | 'module' | 'interface'
    object_type_label: str       # Стойка / Устройство / Модуль / Интерфейс
    equipment_name: str          # имя устройства или стойки
    site_name: str
    group_name: str
    interface_name: str          # заполнено только для object_type == 'interface'
    cable_display: str
    cable_descr: str
    ip_address: str
    start: dt.datetime
    end: Optional[dt.datetime]   # None, если инцидент остался открытым (обрезка не проводилась)
    end_clipped: dt.datetime     # end либо граница периода, для расчёта длительности
    duration: dt.timedelta
    comments: str
    cause: str                   # значение IncidentCauseChoices (человекочитаемое)
    contact_name: str = ""


def format_duration(td: dt.timedelta) -> str:
    total_seconds = max(int(td.total_seconds()), 0)
    hours, rem = divmod(total_seconds, 3600)
    minutes, sec = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{sec:02d}"


def format_date(d: Optional[dt.datetime]) -> str:
    if not d:
        return ""
    from django.utils import timezone
    return timezone.localtime(d).strftime("%d.%m.%Y %H:%M:%S")


def resolve_incidents(queryset, period_start: dt.datetime, period_end: dt.datetime):
    """
    Возвращает список ResolvedIncident для всех инцидентов, пересекающих
    [period_start, period_end]: start <= period_end И (end >= period_start ИЛИ открыт).
    Даты в результате обрезаны по границам периода.
    Поддерживает все 4 типа привязки инцидента: Device, Interface, Module, Rack.
    """
    qs = queryset.filter(start_date__lte=period_end).filter(
        Q(end_date__gte=period_start) | Q(end_date__isnull=True)
    ).distinct().select_related('assigned_object_type', 'assigned_contact')

    device_cache: dict = {}
    results = []

    for incident in qs:
        obj = incident.assigned_object
        if obj is None:
            continue

        cable = None
        interface_name = ""
        device_id = None

        if isinstance(obj, Device):
            object_type = 'device'
            device_id = obj.pk
        elif isinstance(obj, Interface):
            object_type = 'interface'
            device_id = obj.device_id
            interface_name = str(obj)
            cable = obj.cable
        elif isinstance(obj, Module):
            object_type = 'module'
            device_id = obj.device_id
        elif isinstance(obj, Rack):
            object_type = 'rack'
        else:
            continue

        if object_type == 'rack':
            if not obj.site_id:
                continue
            site = obj.site
            site_name = site.name
            if obj.location:
                site_name = f"{site_name}, {obj.location.name}"
            equipment_name = obj.name
            ip_address = ""
        else:
            if device_id not in device_cache:
                try:
                    device_cache[device_id] = Device.objects.select_related(
                        'site', 'site__group', 'location', 'primary_ip4'
                    ).get(pk=device_id)
                except Device.DoesNotExist:
                    continue
            device = device_cache[device_id]

            if not device.site_id:
                continue
            site = device.site

            site_name = site.name
            if device.location:
                site_name = f"{site_name}, {device.location.name}"

            equipment_name = device.name or ""
            ip_address = ""
            if device.primary_ip4:
                ip_address = str(device.primary_ip4.address).replace("/32", "")

        group_name = site.group.name if site.group_id else "Без группы"

        raw_start = incident.start_date
        raw_end = incident.end_date

        start = period_start if (raw_start and raw_start < period_start) else raw_start
        end_clipped = period_end if (not raw_end or raw_end > period_end) else raw_end
        duration = (end_clipped - start) if start else dt.timedelta()

        contact_name = ""
        if incident.assigned_contact_id:
            contact_name = str(incident.assigned_contact)

        results.append(ResolvedIncident(
            incident_id=incident.pk,
            object_type=object_type,
            object_type_label=OBJECT_TYPE_LABELS[object_type],
            equipment_name=equipment_name,
            site_name=site_name,
            group_name=group_name,
            interface_name=interface_name,
            cable_display=str(cable) if cable else "",
            cable_descr=(cable.description if cable else "") or "",
            ip_address=ip_address,
            start=start,
            end=raw_end,
            end_clipped=end_clipped,
            duration=duration,
            comments=incident.comments or "",
            cause=incident.cause,
            contact_name=contact_name,
        ))

    return results


def make_period(date_from: dt.date, date_to: dt.date):
    """date/date -> (aware datetime start 00:00:00, aware datetime end 23:59:59)."""
    from django.utils import timezone
    tz = timezone.get_current_timezone()
    period_start = timezone.make_aware(dt.datetime.combine(date_from, dt.time.min), tz)
    period_end = timezone.make_aware(dt.datetime.combine(date_to, dt.time.max), tz)
    return period_start, period_end


def xlsx_response(workbook, filename: str):
    from io import BytesIO
    from django.http import HttpResponse

    buf = BytesIO()
    workbook.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def apply_borders(ws, min_row, max_row, min_col, max_col):
    from openpyxl.styles import Border, Side
    thin = Side(border_style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
        for cell in row:
            cell.border = border


def autosize_columns(ws, columns):
    for col in columns:
        max_len = 0
        for cell in ws[col]:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col].width = min(max(max_len + 2, 10), 50)
