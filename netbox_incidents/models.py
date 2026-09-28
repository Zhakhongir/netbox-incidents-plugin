from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import NetBoxModel
from .choices import IncidentStatusChoices, IncidentCauseChoices

# Модели, к которым может быть привязан инцидент.
ALLOWED_OBJECT_TYPES = ('device', 'interface', 'module', 'rack')


class Incident(NetBoxModel):
    assigned_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.PROTECT,
        limit_choices_to=models.Q(
            app_label='dcim',
            model__in=ALLOWED_OBJECT_TYPES
        ),
        verbose_name=_('Тип объекта'),
    )
    assigned_object_id = models.PositiveBigIntegerField()
    assigned_object = GenericForeignKey(
        ct_field='assigned_object_type',
        fk_field='assigned_object_id'
    )
    assigned_contact = models.ForeignKey(
        to='tenancy.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('Контактное лицо'),
    )
    start_date = models.DateTimeField(
        verbose_name=_('Дата начала'),
    )
    end_date = models.DateTimeField(
        verbose_name=_('Дата окончания'),
        blank=True,
        null=True,
    )
    status = models.CharField(
        verbose_name=_('Статус'),
        max_length=50,
        choices=IncidentStatusChoices,
        default=IncidentStatusChoices.default_choice,
    )
    cause = models.CharField(
        verbose_name=_('Причина'),
        max_length=50,
        choices=IncidentCauseChoices,
        default=IncidentCauseChoices.default_choice,
    )
    comments = models.TextField(
        verbose_name=_('Комментарий'),
        blank=True,
    )
    created_by = models.ForeignKey(
        to='users.User',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
        verbose_name=_('Создано пользователем'),
    )

    class Meta:
        ordering = ('-start_date',)
        indexes = (
            models.Index(fields=('assigned_object_type', 'assigned_object_id')),
        )
        verbose_name = _('Инцидент')
        verbose_name_plural = _('Инциденты')

    def __str__(self):
        return f"Инцидент #{self.pk} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse('plugins:netbox_incidents:incident', args=[self.pk])

    def clean(self):
        super().clean()

        if self.assigned_object_type_id and self.assigned_object_type.model not in ALLOWED_OBJECT_TYPES:
            raise ValidationError(
                _("Инциденты можно привязывать только к устройствам, интерфейсам, модулям или стойкам.")
            )

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': _("Дата окончания не может быть раньше даты начала.")
            })

    def get_status_color(self):
        return IncidentStatusChoices.colors.get(self.status)

    def get_cause_color(self):
        return IncidentCauseChoices.colors.get(self.cause)
