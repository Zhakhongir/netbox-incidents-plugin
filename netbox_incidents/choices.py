from django.utils.translation import gettext_lazy as _

from utilities.choices import ChoiceSet


class IncidentStatusChoices(ChoiceSet):
    key = 'Incident.status'
    default_choice = 'open'

    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'

    CHOICES = [
        (STATUS_OPEN, _('Открыто'), 'yellow'),
        (STATUS_CLOSED, _('Закрыто'), 'gray'),
    ]

class IncidentCauseChoices(ChoiceSet):
    key = 'Incident.causes'
    default_choice = 'Planned Maintenance'

    CAUSE_PLANNED = 'Planned Maintenance'
    CAUSE_REPAIR = 'Repair/Configuration Work'
    CAUSE_POWER = 'Power Failure'
    CAUSE_EQUIPMENT = 'Equipment Failure'
    CAUSE_PROVIDER = 'Provider Failure'

    CHOICES = [
        (CAUSE_PLANNED, _('Planned Maintenance'), 'yellow'),
        (CAUSE_REPAIR, _('Repair/Configuration Work'), 'yellow'),
        (CAUSE_POWER, _('Power Failure'), 'red'),
        (CAUSE_EQUIPMENT, _('Equipment Failure'), 'red'),
        (CAUSE_PROVIDER, _('Provider Failure'), 'gray'),
    ]
