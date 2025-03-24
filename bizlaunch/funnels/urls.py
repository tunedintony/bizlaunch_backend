from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CopyJobViewSet, FunnelSystemsAPIView, ProjectViewSet

router = DefaultRouter()
router.register(r"jobs", CopyJobViewSet, basename="copy-job")
router.register(r"projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
    path("systems/", FunnelSystemsAPIView.as_view(), name="funnel-template-systems"),
]
