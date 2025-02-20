# from allauth.account.views import SignupView
# from dj_rest_auth.registration.views import (
#     RegisterView,
#     ResendEmailVerificationView,
#     VerifyEmailView,
# )
# from dj_rest_auth.views import (
#     LogoutView,
#     PasswordResetConfirmView,
#     PasswordResetView,
#     UserDetailsView,
# )
# from django.urls import include, path
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# from bizlaunch.users.views import (
#     CustomVerifyEmailView,
#     email_confirm_redirect,
#     password_reset_confirm_redirect,
#     UserDetailView,
#     ChangePasswordView,
# )

# # Create a router and register the TeamMemberViewSet

urlpatterns = [
#     path("change-password/", ChangePasswordView.as_view(), name="change-password"),
#     path("admin/change-password/<uuid:uuid>/", AdminChangePasswordView.as_view(), name="admin-change-password"),
#     path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
#     path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
#     path("register/", RegisterView.as_view(), name="rest_register"),
#     path("me/", UserDetailsView.as_view(), name="rest_user_details"),
#     path("register/resend-email/", ResendEmailVerificationView.as_view(), name="rest_resend_email"),
#     path("account-confirm-email/<str:key>/", email_confirm_redirect, name="account_confirm_email"),
#     path("account-confirm-email/", CustomVerifyEmailView.as_view(), name="account_email_verification_sent"),
#     path("password/reset/", PasswordResetView.as_view() , name="account_reset_password"),
#     path(
#         "password/reset/confirm/<str:uidb64>/<str:token>/",
#         password_reset_confirm_redirect,
#         name="password_reset_confirm",
#     ),
#     path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
