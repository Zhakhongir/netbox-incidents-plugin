from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete
from django.dipatch import receiver

from dcim.models import Device, Interface, Module, Rack

from .models import Incident

@receiver(pre_delete, sender=Device)
@receiver(pre_delete, sender=Interface)
@receiver(pre_delete, sender=Module)
@receiver(pre_delete, sender=Rack)
def delete_incidents_with_object(sender, instance, **kwargs):
  Incident.object.filter(
    assigned_object_type=ContentType.object.get_for_model(sender),
    assigned_object_id=instance.pk,
  ).delete()
