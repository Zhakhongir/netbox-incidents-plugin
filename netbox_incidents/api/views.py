from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(NetBoxModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    filterset_class = filtersets.IncidentFilterSet
