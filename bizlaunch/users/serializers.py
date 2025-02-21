from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(
                {"new_password2": "Passwords do not match."},
            )
        return data

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password1"])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        try:
            EmailAddress.objects.get(user=user, verified=True)
        except EmailAddress.DoesNotExist:
            raise AuthenticationFailed("Email not verified")

        return data


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid",
            "email",
            "created_at",
            "updated_at",
            "last_login",
        )
        read_only_fields = ("email", "created_at", "updated_at", "last_login")
