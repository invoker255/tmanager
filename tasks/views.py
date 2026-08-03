from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Task
from .serializers import TaskSerializer, RegisterSerializer
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'deadline']
    ordering = ['-created_at']
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        logger.info(f'User {self.request.user} created a new task #{task.id}')
    def perform_update(self, serializer):
        task = serializer.save(user=self.request.user)
        logger.info(f'User {self.request.user} updated task #{task.id}')
    def perform_destroy(self, instance):
        task_id = instance.id
        task_title = instance.title
        instance.delete()
        logger.info(f'User {self.request.user} deleted task {task_title} #{task_id}')


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "token": token.key,
            "message": "User registered successfully",
        }, status=status.HTTP_201_CREATED)