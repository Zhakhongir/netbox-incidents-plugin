from django.urls import include, path

from utilities.urls import get_model_urls

from . import views 

app_name = 'netbox_incidents'

urlpatterns = [
    path('incidents/', include(get_model_urls('netbox_incidents', 'incident', detail=False))),
    path('incidents/<int:pk>/', include(get_model_urls('netbox_incidents', 'incident'))),
    path('reports/', views.ReportsIndexView.as_view(), name='reports'),
    path('reports/<slug:report_slug>/generate/', views.ReportGenerateView.as_view(), name='report_generate'),
]
