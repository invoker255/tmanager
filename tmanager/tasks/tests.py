from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from tasks.models import Task

TASKS_URL = '/api/tasks/'
COMMAND_SEND = 'tasks.management.commands.send_deadline_reminders.send_deadline_reminder_email'

pytestmark = pytest.mark.django_db


def make_task(user, **kwargs):
    kwargs.setdefault('title', 'Task')
    return Task.objects.create(user=user, **kwargs)


def in_hours(hours):
    return timezone.now() + timedelta(hours=hours)


def test_health_endpoint(api_client):
    response = api_client.get('/api/health/')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_tasks_require_authentication(api_client):
    assert api_client.get(TASKS_URL).status_code == 401
    assert api_client.post(TASKS_URL, {'title': 'x'}, format='json').status_code == 401


def test_create_task_assigns_current_user(auth_client, user):
    response = auth_client.post(
        TASKS_URL,
        {
            'title': 'Write tests',
            'priority': 'high',
            'category': 'Work',
            'deadline': in_hours(72).isoformat(),
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data['user'] == user.username
    assert response.data['status'] == 'todo'
    assert response.data['days_left'].startswith('Days left:')
    assert Task.objects.get(pk=response.data['id']).user == user


def test_create_task_without_deadline(auth_client):
    response = auth_client.post(TASKS_URL, {'title': 'No deadline'}, format='json')
    assert response.status_code == 201
    assert response.data['deadline'] is None
    assert response.data['days_left'] is None


def test_create_task_rejects_past_deadline(auth_client):
    response = auth_client.post(
        TASKS_URL,
        {'title': 'Too late', 'deadline': in_hours(-5).isoformat()},
        format='json',
    )
    assert response.status_code == 400
    assert 'deadline' in response.data


def test_create_task_rejects_invalid_status(auth_client):
    response = auth_client.post(TASKS_URL, {'title': 'Bad', 'status': 'bogus'}, format='json')
    assert response.status_code == 400
    assert 'status' in response.data


def test_create_task_requires_title(auth_client):
    response = auth_client.post(TASKS_URL, {'description': 'no title'}, format='json')
    assert response.status_code == 400
    assert 'title' in response.data


def test_days_left_reports_missed_deadline(auth_client, user):
    task = make_task(user, deadline=in_hours(-3))
    response = auth_client.get(f'{TASKS_URL}{task.id}/')
    assert response.status_code == 200
    assert response.data['days_left'] == 'Missed'


def test_users_only_see_their_own_tasks(auth_client, make_user):
    other = make_user('bob')
    foreign = make_task(other, title='Bob private task')
    assert auth_client.get(TASKS_URL).data['count'] == 0
    assert auth_client.get(f'{TASKS_URL}{foreign.id}/').status_code == 404
    assert auth_client.patch(f'{TASKS_URL}{foreign.id}/', {'title': 'hacked'}, format='json').status_code == 404
    assert auth_client.delete(f'{TASKS_URL}{foreign.id}/').status_code == 404
    foreign.refresh_from_db()
    assert foreign.title == 'Bob private task'


def test_list_is_paginated(auth_client, user):
    for index in range(12):
        make_task(user, title=f'Task {index}')
    first = auth_client.get(TASKS_URL).data
    assert first['count'] == 12
    assert len(first['results']) == 10
    assert first['next'] is not None
    second = auth_client.get(TASKS_URL, {'page': 2}).data
    assert len(second['results']) == 2
    assert second['next'] is None


def test_filter_by_status_priority_and_category(auth_client, user):
    make_task(user, title='A', status='done', priority='low', category='Work')
    make_task(user, title='B', status='todo', priority='high', category='Personal')
    make_task(user, title='C', status='todo', priority='high', category='Work')

    by_status = auth_client.get(TASKS_URL, {'status': 'done'}).data['results']
    assert [t['title'] for t in by_status] == ['A']

    by_priority = auth_client.get(TASKS_URL, {'priority': 'high'}).data['results']
    assert {t['title'] for t in by_priority} == {'B', 'C'}

    by_category = auth_client.get(TASKS_URL, {'category': 'Work'}).data['results']
    assert {t['title'] for t in by_category} == {'A', 'C'}

    combined = auth_client.get(TASKS_URL, {'priority': 'high', 'category': 'Work'}).data['results']
    assert [t['title'] for t in combined] == ['C']


def test_search_by_title_and_description(auth_client, user):
    make_task(user, title='Buy milk')
    make_task(user, title='Write report', description='quarterly numbers')
    assert [t['title'] for t in auth_client.get(TASKS_URL, {'search': 'milk'}).data['results']] == ['Buy milk']
    assert [t['title'] for t in auth_client.get(TASKS_URL, {'search': 'quarterly'}).data['results']] == ['Write report']


def test_ordering_by_deadline(auth_client, user):
    make_task(user, title='Late', deadline=in_hours(72))
    make_task(user, title='Soon', deadline=in_hours(24))
    make_task(user, title='Middle', deadline=in_hours(48))
    ascending = auth_client.get(TASKS_URL, {'ordering': 'deadline'}).data['results']
    assert [t['title'] for t in ascending] == ['Soon', 'Middle', 'Late']
    descending = auth_client.get(TASKS_URL, {'ordering': '-deadline'}).data['results']
    assert [t['title'] for t in descending] == ['Late', 'Middle', 'Soon']


def test_update_status(auth_client, user):
    task = make_task(user)
    response = auth_client.patch(f'{TASKS_URL}{task.id}/', {'status': 'done'}, format='json')
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == 'done'


def test_changing_deadline_resets_reminder_flag(auth_client, user):
    task = make_task(user, deadline=in_hours(24), reminder_sent=True)
    response = auth_client.patch(
        f'{TASKS_URL}{task.id}/',
        {'deadline': in_hours(120).isoformat()},
        format='json',
    )
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.reminder_sent is False


def test_updating_other_fields_keeps_reminder_flag(auth_client, user):
    task = make_task(user, deadline=in_hours(24), reminder_sent=True)
    auth_client.patch(f'{TASKS_URL}{task.id}/', {'title': 'Renamed'}, format='json')
    task.refresh_from_db()
    assert task.reminder_sent is True


def test_delete_task(auth_client, user):
    task = make_task(user)
    response = auth_client.delete(f'{TASKS_URL}{task.id}/')
    assert response.status_code == 204
    assert not Task.objects.filter(pk=task.pk).exists()


def test_reminder_sent_when_deadline_is_inside_window(user, mailoutbox):
    task = make_task(user, title='Pay rent', deadline=in_hours(10))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [user.email]
    assert 'Pay rent' in mailoutbox[0].subject
    task.refresh_from_db()
    assert task.reminder_sent is True


def test_reminder_not_sent_outside_window(user, mailoutbox):
    task = make_task(user, deadline=in_hours(48))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 0
    task.refresh_from_db()
    assert task.reminder_sent is False


def test_reminder_respects_longer_user_window(user, mailoutbox):
    user.user_settings.reminder_hours_before = 72
    user.user_settings.save()
    make_task(user, deadline=in_hours(48))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 1


def test_reminder_disabled_by_user(user, mailoutbox):
    user.user_settings.reminder_hours_before = 0
    user.user_settings.save()
    make_task(user, deadline=in_hours(2))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 0


def test_reminder_skips_done_tasks(user, mailoutbox):
    make_task(user, status='done', deadline=in_hours(2))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 0


def test_reminder_skips_unverified_users(make_user, mailoutbox):
    unverified = make_user('ghost', verified=False)
    make_task(unverified, deadline=in_hours(2))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 0


def test_reminder_skips_past_deadlines(user, mailoutbox):
    make_task(user, deadline=in_hours(-2))
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 0


def test_reminder_is_sent_only_once(user, mailoutbox):
    make_task(user, deadline=in_hours(5))
    call_command('send_deadline_reminders')
    call_command('send_deadline_reminders')
    assert len(mailoutbox) == 1


def test_reminder_failure_keeps_task_pending(user, monkeypatch):
    def boom(user, task):
        raise RuntimeError('smtp down')

    monkeypatch.setattr(COMMAND_SEND, boom)
    task = make_task(user, deadline=in_hours(5))
    call_command('send_deadline_reminders')
    task.refresh_from_db()
    assert task.reminder_sent is False



def test_api_schema_and_docs_are_available(api_client):
    assert api_client.get('/api/schema/').status_code == 200
    assert api_client.get('/api/docs/').status_code == 200
