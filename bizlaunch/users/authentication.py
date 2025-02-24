from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class CustomJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        # Validate the token using the parent class method
        validated_token = super().get_validated_token(raw_token)

        # Check if the token is blacklisted
        if BlacklistedToken.objects.filter(token__jti=validated_token["jti"]).exists():
            raise InvalidToken("This token has been blacklisted.")

        return validated_token
