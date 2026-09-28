from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ReportDefinition:
    slug: str
    name: str
    description: str
    period_type: str
    generator: Optional[Callable] = field(default=None)


REPORTS = [
    ReportDefinition(
        slug='general',
        name='Общий отчет',
        description='Инциденты, зафиксированные за период времени',
        period_type='range',
    ),
    ReportDefinition(
        slug='detail',
        name='Детальный отчет',
        description='Подробный отчёт: группа сайтов → причина → тип объекта',
        period_type='range',
    ),
    ReportDefinition(
        slug='statistic',
        name='Статистика',
        description='Количество и время простоя по причинам, в разрезе групп сайтов и типов объектов',
        period_type='range',
    ),
]


def get_report(slug):
    return next((r for r in REPORTS if r.slug == slug), None)


def register_generator(slug, func):
    """Подключить функцию генерации к типу отчёта (вызывается извне при добавлении скрипта)."""
    report = get_report(slug)
    if report:
        report.generator = func


def _wire_generators():
    """Подключает реализованные генераторы отчётов (xlsx) к их слагам."""
    from . import reports_general, reports_detail, reports_statistic
    register_generator('general', reports_general.generate)
    register_generator('detail', reports_detail.generate)
    register_generator('statistic', reports_statistic.generate)


_wire_generators()
