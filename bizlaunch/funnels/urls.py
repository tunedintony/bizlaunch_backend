from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FunnelSystemsAPIView

# router = DefaultRouter()
# router.register(r'systems', SystemTemplateViewSet, basename='system')
# router.register(r'copy-jobs', CopyJobViewSet, basename='copy-job')

urlpatterns = [
    path("funnels/", FunnelSystemsAPIView.as_view(), name="funnel-template-systems"),
]
