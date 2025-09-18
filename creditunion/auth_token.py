from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from creditunion.models import Member, CustomUser  # Adjust if needed

class CustomAuthToken(APIView):
    """
    Custom login view that uses authenticate() directly and returns user + token info.
    """
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'detail': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({'non_field_errors': ['Unable to log in with provided credentials.']},
                            status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)

        try:
            member = user.member_profile
            member_id = member.id
            member_uuid = member.membership_number
            full_name = member.full_name
        except Member.DoesNotExist:
            member_id = None
            full_name = None

        return Response({
            'token': token.key,
            'usid': user.id,
            'username': user.username,
            'is_member': user.is_member,
            'is_admin': user.is_admin,
            'church': user.church.name if user.church else None,
            'member_id': member_id,
            'full_name': full_name,
            'uuid': member_uuid,
            'first_name': user.first_name
        }, status=status.HTTP_200_OK)
