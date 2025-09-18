from datetime import date
import uuid
from django.shortcuts import render

# Create your views here.


# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate
from . models import Member
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
User = get_user_model()






@api_view(['POST'])
def signup(request):
    first_name = request.data.get('first_name')
    username = request.data.get('username')
    email = request.data.get('email', f"{username}@gmail.com")
    password1 = request.data.get('password1')
    password2 = request.data.get('password2')

    # Check if all fields are provided
    if not all([username, email, password1, password2]):
        return Response({'message': 'All fields are required.', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'message': f'{username} already exists', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'message': f'{email} already exists', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    if password1 != password2:
        return Response({'message': 'Password mismatch', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    # Create user securely
    user = User.objects.create_user(username=username, email=email, password=password1, first_name=first_name)
    user.save()
    
    
    # Auto-generate a unique membership number
    membership_number = f"MBR-{uuid.uuid4().hex[:6].upper()}"

    # Create minimal member profile
    Member.objects.create(
        user=user,
        full_name=username,  # Default to username; user can change later
        membership_number=membership_number,
        join_date=date.today(),  # Optional, since auto_now_add handles it
    )

    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    return Response({
        'message': 'Signup Successful, Login to complete registration',
        'status': True,
        'first_name': first_name,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)



@api_view(['POST'])

def signin(request):
    username = request.data.get('username')
    password = request.data.get('password')
    print("Request received:", request.data)

    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'username': user.username,
        'userId': user.id,
        'email': user.email,
        'church': user.church.name if hasattr(user, 'church') and user.church else None,
    })



@api_view(['POST'])
def signout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"message": "logged out successfully", "status": True},
                        status=status.HTTP_205_RESET_CONTENT)
    except KeyError:
        return Response({"message": "Refresh token is required", "status": False},
                        status=status.HTTP_400_BAD_REQUEST)
    except TokenError:
        return Response({"message": "Invalid or expired token", "status": False},
                        status=status.HTTP_400_BAD_REQUEST)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if not user.check_password(current_password):
        return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "New passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({"success": "Password updated successfully"}, status=status.HTTP_200_OK)