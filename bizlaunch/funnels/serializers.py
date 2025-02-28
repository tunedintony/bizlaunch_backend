from rest_framework import serializers

from .models import AdCopy, CopyJob, SystemTemplate


class SystemTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemTemplate
        fields = ["uuid", "name", "image"]
        read_only_fields = fields


class CopyJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CopyJob
        fields = ["system", "client_data", "file", "user_uuid"]
        extra_kwargs = {"user_uuid": {"write_only": True}}


class AdCopyGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdCopy
        fields = ["funnel", "page", "generated_components", "generated_text"]


class CopyJobStatusSerializer(serializers.ModelSerializer):
    results = AdCopyGenerationSerializer(many=True, read_only=True)

    class Meta:
        model = CopyJob
        fields = ["uuid", "status", "results", "created_at", "updated_at"]
        read_only_fields = fields
