import logging

from celery import current_app
from celery.result import AsyncResult
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bizlaunch.funnels.models import CopyJob, Project, SystemTemplate
from bizlaunch.funnels.serializers import (
    CopyJobCreateSerializer,
    CopyJobStatusSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
    SystemTemplateSerializer,
)
from bizlaunch.funnels.tasks import process_copy_job

# Initialize logger
logger = logging.getLogger(__name__)


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
    http_method_names = ["get"]
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


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows projects to be created, updated, listed, or deleted.

    Flow:
    1. On creation, the user provides:
       - An optional name (or one is auto-generated),
       - A system funnel (for the ad copy job),
       - And either text data or a CSV client file.
    2. A copy job is created using the provided system and input, and asynchronous processing is triggered.
    3. The project is then created and linked to that copy job.
    4. Once created, the project’s system (i.e. the copy job’s system) cannot be updated.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = "uuid"

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    @swagger_auto_schema(
        operation_description="List all projects for the authenticated user.",
        responses={200: ProjectSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a project by its UUID.",
        responses={200: ProjectSerializer()},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description=(
            "Create a new project. Provide a name (or leave blank for an auto-generated name), "
            "system UUID, text data, and optional CSV file."
        ),
        request_body=ProjectCreateSerializer,
        responses={201: ProjectSerializer()},
    )
    def create(self, request, *args, **kwargs):
        """
        Handles multipart/form-data requests with file uploads.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except Exception as e:
            logger.error(f"Project creation failed: {str(e)}")
            return Response(
                {"detail": "Error creating project"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @swagger_auto_schema(
        operation_description=(
            "Update a project's name. The copy job (and hence the system) cannot be changed once created."
        ),
        request_body=ProjectSerializer,
        responses={200: ProjectSerializer()},
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Prevent attempts to change the copy_job or its associated system.
        if "copy_job" in request.data or "system" in request.data:
            raise ValidationError("Modifying the copy job or system is not allowed.")
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a project and its associated copy job.",
        responses={204: "No Content"},
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.copy_job:
            self.kill_copy_job_task(instance.copy_job)
            instance.copy_job.delete()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def kill_copy_job_task(self, copy_job):
        """
        Revoke the Celery task associated with the given copy job.
        Uses the celery_task_id stored on the copy job.
        """

        task_id = getattr(copy_job, "celery_task_id", None)
        if task_id:
            try:
                current_app.control.revoke(task_id, terminate=True)
                logger.info(f"Revoked celery task {task_id} for copy job {copy_job.pk}")
            except Exception as e:
                logger.error(f"Failed to revoke task {task_id}: {str(e)}")
