from netbox.api.routers import NetBoxRouter

from .views import IncidentViewSet

router = NetBoxRouter()
router.register('incidents', IncidentViewSet)

urlpatterns = router.urls
