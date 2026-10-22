import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token

from users.models import User
from users.validators import ComplexityValidator

REGISTER_URL = '/api/register/'
LOGIN_URL = '/api/login/'
RESEND_URL = '/api/resend-verification/'
VERIFY_URL = '/api/users/verify-email/'
ME_URL = '/api/users/me/'
SETTINGS_URL = '/api/users/settings/'
PASSWORD_URL = '/api/users/change-password/'
STRONG = 'Str0ng!Pass1'

pytestmark = pytest.mark.django_db


def test_complexity_validator_accepts_strong_password():
    ComplexityValidator.validate(STRONG)


@pytest.mark.parametrize('password', ['alllower1!', 'ALLUPPER1!', 'NoDigits!!', 'NoSpecial11'])
def test_complexity_validator_rejects_weak_password(password):
    with pytest.raises(ValidationError):
        ComplexityValidator.validate(password)


def test_register_creates_unverified_user_and_sends_email(api_client, mailoutbox):
    response = api_client.post(
        REGISTER_URL,
        {'username': 'newuser', 'email': 'new@example.com', 'password': STRONG},
        format='json',
    )
    assert response.status_code == 201
    assert response.data['email_sent'] is True
    assert 'token' not in response.data
    user = User.objects.get(username='newuser')
    assert user.is_email_verified is False
    assert user.user_settings.reminder_hours_before == 24
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['new@example.com']
    assert '/verify/' in mailoutbox[0].body


@pytest.mark.parametrize(
    'password',
    ['Sh0rt!a', 'alllowercase1!', 'ALLUPPERCASE1!', 'NoNumbers!!', 'NoSpecial123'],
)
def test_register_rejects_weak_passwords(api_client, password):
    response = api_client.post(
        REGISTER_URL,
        {'username': 'weakling', 'email': 'weak@example.com', 'password': password},
        format='json',
    )
    assert response.status_code == 400
    assert 'password' in response.data
    assert not User.objects.filter(username='weakling').exists()


def test_register_rejects_password_similar_to_username(api_client):
    response = api_client.post(
        REGISTER_URL,
        {'username': 'steptest4', 'email': 'steptest4@example.com', 'password': 'steptest4aA1!'},
        format='json',
    )
    assert response.status_code == 400
    assert 'password' in response.data


def test_register_rejects_duplicate_username(api_client, user):
    response = api_client.post(
        REGISTER_URL,
        {'username': user.username, 'email': 'other@example.com', 'password': STRONG},
        format='json',
    )
    assert response.status_code == 400
    assert 'username' in response.data


def test_register_rejects_duplicate_email(api_client, user):
    response = api_client.post(
        REGISTER_URL,
        {'username': 'other', 'email': user.email, 'password': STRONG},
        format='json',
    )
    assert response.status_code == 400
    assert 'email' in response.data


def test_register_survives_email_failure(api_client, monkeypatch):
    def boom(user):
        raise RuntimeError('smtp down')

    monkeypatch.setattr('tasks.views.send_verification_email', boom)
    response = api_client.post(
        REGISTER_URL,
        {'username': 'mailfail', 'email': 'mailfail@example.com', 'password': STRONG},
        format='json',
    )
    assert response.status_code == 201
    assert response.data['email_sent'] is False
    assert User.objects.filter(username='mailfail').exists()


def test_login_requires_verified_email(api_client, make_user):
    make_user('unverified', verified=False)
    response = api_client.post(LOGIN_URL, {'username': 'unverified', 'password': STRONG}, format='json')
    assert response.status_code == 403
    assert response.data['code'] == 'email_not_verified'
    assert 'token' not in response.data


def test_login_returns_token_for_verified_user(api_client, user):
    response = api_client.post(LOGIN_URL, {'username': user.username, 'password': STRONG}, format='json')
    assert response.status_code == 200
    assert response.data['token'] == Token.objects.get(user=user).key


def test_login_rejects_wrong_password(api_client, user):
    response = api_client.post(LOGIN_URL, {'username': user.username, 'password': 'Wrong!Pass1'}, format='json')
    assert response.status_code == 400
    assert 'Error' in response.data


def test_verify_email_marks_user_verified(api_client, make_user):
    user = make_user('toverify', verified=False)
    payload = {
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    }
    response = api_client.post(VERIFY_URL, payload, format='json')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_email_verified is True


def test_verify_email_rejects_bad_token(api_client, make_user):
    user = make_user('badtoken', verified=False)
    payload = {'uid': urlsafe_base64_encode(force_bytes(user.pk)), 'token': 'not-a-real-token'}
    response = api_client.post(VERIFY_URL, payload, format='json')
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.is_email_verified is False


def test_verify_email_with_empty_payload_is_400_not_500(api_client):
    response = api_client.post(VERIFY_URL, {}, format='json')
    assert response.status_code == 400


def test_resend_sends_email_to_unverified_user(api_client, make_user, mailoutbox):
    make_user('resendme', verified=False)
    response = api_client.post(RESEND_URL, {'email': 'resendme@example.com'}, format='json')
    assert response.status_code == 200
    assert len(mailoutbox) == 1


def test_resend_does_not_reveal_unknown_email(api_client, mailoutbox):
    response = api_client.post(RESEND_URL, {'email': 'nobody@example.com'}, format='json')
    assert response.status_code == 200
    assert 'message' in response.data
    assert len(mailoutbox) == 0


def test_resend_skips_verified_user(api_client, user, mailoutbox):
    response = api_client.post(RESEND_URL, {'email': user.email}, format='json')
    assert response.status_code == 200
    assert len(mailoutbox) == 0


def test_resend_requires_email(api_client):
    response = api_client.post(RESEND_URL, {}, format='json')
    assert response.status_code == 400


def test_resend_is_rate_limited(api_client, make_user):
    make_user('limited', verified=False)
    statuses = [
        api_client.post(RESEND_URL, {'email': 'limited@example.com'}, format='json').status_code
        for _ in range(4)
    ]
    assert statuses == [200, 200, 200, 429]


def test_me_requires_authentication(api_client):
    assert api_client.get(ME_URL).status_code == 401


def test_me_returns_profile(auth_client, user):
    response = auth_client.get(ME_URL)
    assert response.status_code == 200
    assert response.data['username'] == user.username
    assert response.data['email'] == user.email
    assert response.data['is_email_verified'] is True


def test_changing_email_requires_new_verification(auth_client, user, mailoutbox):
    response = auth_client.patch(ME_URL, {'email': 'changed@example.com'}, format='json')
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email == 'changed@example.com'
    assert user.is_email_verified is False
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['changed@example.com']


def test_settings_defaults(auth_client):
    response = auth_client.get(SETTINGS_URL)
    assert response.status_code == 200
    assert response.data == {'reminder_hours_before': 24, 'theme': 'dark'}


def test_settings_update(auth_client, user):
    response = auth_client.patch(SETTINGS_URL, {'reminder_hours_before': 12, 'theme': 'light'}, format='json')
    assert response.status_code == 200
    user.user_settings.refresh_from_db()
    assert user.user_settings.reminder_hours_before == 12
    assert user.user_settings.theme == 'light'


@pytest.mark.parametrize('payload', [{'reminder_hours_before': 5}, {'theme': 'blue'}])
def test_settings_reject_invalid_values(auth_client, payload):
    response = auth_client.patch(SETTINGS_URL, payload, format='json')
    assert response.status_code == 400


def test_change_password_rotates_token(auth_client, api_client, user):
    old_key = Token.objects.get(user=user).key
    response = auth_client.post(
        PASSWORD_URL,
        {'old_password': STRONG, 'new_password': 'N3wStrong!Pass'},
        format='json',
    )
    assert response.status_code == 200
    assert response.data['token'] != old_key
    assert not Token.objects.filter(key=old_key).exists()
    login = api_client.post(LOGIN_URL, {'username': user.username, 'password': 'N3wStrong!Pass'}, format='json')
    assert login.status_code == 200
    assert login.data['token'] == response.data['token']


def test_change_password_old_token_stops_working(auth_client):
    auth_client.post(PASSWORD_URL, {'old_password': STRONG, 'new_password': 'N3wStrong!Pass'}, format='json')
    assert auth_client.get(ME_URL).status_code == 401


def test_change_password_rejects_wrong_old_password(auth_client):
    response = auth_client.post(
        PASSWORD_URL,
        {'old_password': 'Wrong!Pass1', 'new_password': 'N3wStrong!Pass'},
        format='json',
    )
    assert response.status_code == 400
    assert 'old_password' in response.data


def test_change_password_rejects_weak_new_password(auth_client):
    response = auth_client.post(PASSWORD_URL, {'old_password': STRONG, 'new_password': 'weak'}, format='json')
    assert response.status_code == 400
    assert 'new_password' in response.data