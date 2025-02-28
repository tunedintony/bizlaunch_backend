from rest_framework import serializers

from .models import AdCopy, CopyJob, SystemTemplate


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
        source="ad_copies",
        allow_null=True,
    )

    class Meta:
        model = CopyJob
        fields = ["uuid", "user", "status", "results", "created_at", "updated_at"]
        read_only_fields = fields
