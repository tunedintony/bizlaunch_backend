import random
import string

from rest_framework import serializers

from bizlaunch.funnels.models import AdCopy, CopyJob, Project, SystemTemplate


class SystemTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemTemplate
        fields = ["uuid", "name", "image"]
        read_only_fields = fields


class CopyJobCreateSerializer(serializers.ModelSerializer):
    text_data = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CopyJob
        fields = ["system", "client_file", "text_data"]

    def validate(self, attrs):
        if not attrs.get("text_data"):
            raise serializers.ValidationError("The 'text_data' field is required.")
        if attrs.get("client_file") and not attrs["client_file"].name.endswith(".csv"):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return attrs

    def create(self, validated_data):
        text_data = validated_data.pop("text_data")
        validated_data["client_data"] = {"user_input": text_data}
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class AdCopyGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdCopy
        fields = ["funnel", "page", "copy_text", "copy_json"]


class CopyJobStatusSerializer(serializers.ModelSerializer):
    results = AdCopyGenerationSerializer(
        many=True,
        read_only=True,
        source="generated_copies",
        allow_null=True,
    )

    class Meta:
        model = CopyJob
        fields = ["uuid", "user", "status", "results", "created_at", "updated_at"]
        read_only_fields = fields


class SystemTemplateNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for SystemTemplate.
    Only exposes the uuid and name fields.
    """

    class Meta:
        model = SystemTemplate
        fields = ["uuid", "name"]


class CopyJobNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for CopyJob.
    Only returns the uuid, status, and the linked system using a nested serializer.
    """

    system = SystemTemplateNestedSerializer(read_only=True)

    class Meta:
        model = CopyJob
        fields = ["uuid", "status", "system"]


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a project.

    Expected fields:
    - name: Optional; if not provided, a random name will be generated.
    - system: The selected system funnel (required).
    - text_data: Write-only field. Either text_data or client_file must be provided.
    - client_file: Write-only field. Optional CSV file. Either this or text_data is required.
    """

    text_data = serializers.CharField(write_only=True, required=False, allow_blank=True)
    client_file = serializers.FileField(
        write_only=True, required=False, allow_null=True
    )
    system = serializers.PrimaryKeyRelatedField(
        queryset=SystemTemplate.objects.all(), write_only=True
    )
    copy_job = CopyJobNestedSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["uuid", "name", "system", "text_data", "client_file", "copy_job"]
        read_only_fields = ["uuid", "copy_job"]

    def validate(self, attrs):
        text = attrs.get("text_data", "").strip()
        file = attrs.get("client_file")
        if not text and not file:
            raise serializers.ValidationError(
                "Either text_data or client_file is required."
            )
        if file and not file.name.endswith(".csv"):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return attrs

    def create(self, validated_data):
        # Extract fields for the copy job creation.
        text = validated_data.pop("text_data", "").strip()
        client_file = validated_data.pop("client_file", None)
        system = validated_data.pop("system")
        request = self.context.get("request")
        user = request.user if request else None

        # If name is not provided, assign a random name.
        name = validated_data.get("name")
        if not name:
            random_str = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
            name = f"Project {random_str}"
        validated_data["name"] = name

        # Build the client_data payload.
        client_data = {}
        if text:
            client_data["user_input"] = text

        # Create the copy job. Note that the system is associated here.
        copy_job = CopyJob.objects.create(
            system=system, client_data=client_data, user=user, client_file=client_file
        )

        # Create the project and link the copy job.
        project = Project.objects.create(user=user, copy_job=copy_job, **validated_data)

        # Trigger asynchronous processing of the copy job.
        from bizlaunch.funnels.tasks import (
            process_copy_job,  # local import to avoid circular dependency
        )

        task = process_copy_job.delay(copy_job.uuid)
        # Save the celery task id on the copy job.
        copy_job.celery_task_id = task.id
        copy_job.save(update_fields=["celery_task_id"])

        return project


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and listing a project.
    It returns project details along with the linked copy job.
    """

    copy_job = CopyJobNestedSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "uuid",
            "name",
            "copy_job",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "copy_job",
            "created_at",
            "updated_at",
        ]
