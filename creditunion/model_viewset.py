from rest_framework import viewsets, permissions, generics
from rest_framework.decorators import api_view
from .models import Transaction
from .serializers import TransactionSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser, Church
from .serializers import MemberSerializer, MemberProfileSerializer, ChurchSerializer



class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transactions.
    Automatically tracks the account officer recording the transaction.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)  # don't raise so we can inspect
        if not serializer.is_valid():
            print(serializer.errors)  # log validation errors
            return Response(serializer.errors, status=400)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)




class AllMembersAPIView(APIView):
    """
    Returns a list of all users who are members (not staff or superusers).
    This helps account officers select the correct member when adding a transaction.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        members = CustomUser.objects.filter(is_member=True, is_active=True)
        serializer = MemberSerializer(members, many=True)
        return Response(serializer.data)




class UserTransactionListView(APIView):
    """
    Returns all transactions created by the currently logged-in user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        transactions = Transaction.objects.filter(member=user).order_by('-date')
        data = TransactionSerializer(transactions, many=True).data
        return Response(data)



class MemberProfileView(generics.RetrieveUpdateAPIView):
    """
    View for members to retrieve and update their profile.
    Only authenticated users can access their own profile.
    """
    serializer_class = MemberProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure we fetch the logged-in user's Member instance
        return self.request.user.member



@api_view(['GET'])
def church_list(request):
    """
    Returns list of all churches in the system.
    """
    churches = Church.objects.all()
    serializer = ChurchSerializer(churches, many=True)
    return Response(serializer.data)