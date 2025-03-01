from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bizlaunch.funnels.models import CopyJob, SystemTemplate
from bizlaunch.funnels.serializers import (
    CopyJobCreateSerializer,
    CopyJobStatusSerializer,
    SystemTemplateSerializer,
)
from bizlaunch.funnels.tasks import process_copy_job

class FunnelSystemsAPIView(APIView):
    """
    Returns the UUIDs of all funnel systems.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        systems = SystemTemplate.objects.all()
        serializer = SystemTemplateSerializer(systems, many=True)
        return Response(serializer.data)


class CopyJobViewSet(viewsets.ModelViewSet):
    http_method_names = ["post", "get", "head"]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = "uuid"

    def get_queryset(self):
        return CopyJob.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return CopyJobCreateSerializer
        return CopyJobStatusSerializer

    @swagger_auto_schema(
        operation_description="Create a new CopyJob with optional file upload.",
        request_body=CopyJobCreateSerializer,
        responses={
            201: CopyJobStatusSerializer,
            400: "Validation Error",
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Trigger async processing
        process_copy_job.delay(instance.uuid)

        response_serializer = CopyJobStatusSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
