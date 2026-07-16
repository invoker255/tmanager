from rest_framework import serializers
from .models import Task
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'category', 'created_at', 'deadline', 'user']

    @staticmethod
    def validate_deadline(value):
        if value and value < timezone.now():
            raise serializers.ValidationError('Deadline date cannot be in the past!')
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        email = validated_data.pop('email', '')
        return User.objects.create_user(email=email, password=password, **validated_data)