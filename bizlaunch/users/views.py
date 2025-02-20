import base64
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from decouple import config
from dj_rest_auth.registration.serializers import (
    SocialLoginSerializer,
    VerifyEmailSerializer,
)
from dj_rest_auth.registration.views import SocialLoginView, VerifyEmailView
from dj_rest_auth.serializers import JWTSerializer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import viewsets as RFViewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from bizlaunch.users.models import User
from bizlaunch.users.serializers import (
    AdminChangePasswordSerializer,
    ChangePasswordSerializer,
    EmailVerificationResponseSerializer,
    GoogleSocialLoginResponseSerializer,
    GoogleSocialLoginSerializer,
    MemberRegisterSerializer,
    RouteResponseSerializer,
    TeamInviteListResponseSerializer,
    TeamInviteSerializer,
    TeamMemberSerializer,
    UserDetailSerializer,
)
from bizlaunch.users.signup_router import Router
from bizlaunch.users.slack_service import SlackService
from bizlaunch.users.swagger_docs import (
    admin_change_password_docs,
    change_password_docs,
    team_member_toggle_docs,
)
from bizlaunch.users.tasks import expire_team_invite_task


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(**change_password_docs)
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Password changed successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(RetrieveAPIView):
    """
    View to retrieve user details.
    """

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Retrieve the currently authenticated user
        return self.request.user


def email_confirm_redirect(request, key):
    return HttpResponseRedirect(f"{settings.EMAIL_CONFIRM_REDIRECT_BASE_URL}{key}/")


def password_reset_confirm_redirect(request, uidb64, token):
    return HttpResponseRedirect(
        f"{settings.PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL}{uidb64}/{token}/"
    )
