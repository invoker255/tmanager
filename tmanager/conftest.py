import pytest
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def factory(username='alice', email=None, password='Str0ng!Pass1', verified=True):
        user = User.objects.create_user(
            username=username,
            email=email or f'{username}@example.com',
            password=password,
        )
        user.is_email_verified = verified
        user.save(update_fields=['is_email_verified'])
        return user

    return factory


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client
