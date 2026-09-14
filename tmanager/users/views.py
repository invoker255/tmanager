from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model

User = get_user_model()

class VerifyEmailView(APIView):

    def post(self ,request):
        uid=request.data.get('uid')
        token=request.data.get('token')

        try:
            user_id=force_str(urlsafe_base64_decode(uid))
            user=User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user=None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_email_verified=True
            user.save()
            return Response({'message': 'Имеил подтвержден'}, status=status.HTTP_200_OK)
        return Response({'Error': 'Ссылка недействительна или устарела'}, status=status.HTTP_400_BAD_REQUEST)
