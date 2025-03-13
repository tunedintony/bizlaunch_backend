from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CopyJobViewSet, FunnelSystemsAPIView

router = DefaultRouter()
router.register(r"copy-jobs", CopyJobViewSet, basename="copy-job")

urlpatterns = [
    path("", include(router.urls)),
    path("funnels/", FunnelSystemsAPIView.as_view(), name="funnel-template-systems"),
]
