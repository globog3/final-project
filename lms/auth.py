import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer
from ninja.errors import HttpError

User = get_user_model()

def generate_token(user):
    """
    Generate JWT access token for a user
    """
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRY_MINUTES)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            if not user_id:
                return None
            user = User.objects.get(id=user_id)
            return user
        except (jwt.PyJWTError, User.DoesNotExist):
            return None


# Reusable auth instance
jwt_auth = JWTAuth()


def role_required(roles):
    """
    Helper function or check to enforce roles in endpoints.
    In Django Ninja, you can check request.auth (which is the user model returned by JWTAuth).
    """
    def checker(request):
        if not request.auth:
            raise HttpError(401, "Unauthorized")
        if request.auth.role not in roles:
            raise HttpError(403, f"Forbidden: Requires one of these roles: {roles}")
        return True
    return checker
