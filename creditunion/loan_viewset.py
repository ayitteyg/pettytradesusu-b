from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

from .models import Loan, CustomUser
from .serializers import LoanSerializer,  LoanRepaymentSerializer, LoanRepayment
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class LoanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing loan operations:
    - Create loan request (by member)
    - List user loans
    - Admins can approve/reject/cancel
    """
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Limit users to see only their own loans,
        unless staff or superuser.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Loan.objects.all()
        return Loan.objects.filter(member=user)

    
    
    def perform_create(self, serializer):
        """
        Called when a loan is requested.
        Prevents a member from having more than one pending loan.
        Member can be selected by account officer or be the requester.
        """
        member = serializer.validated_data.get("member")

        if not member:
            raise ValidationError({"member": "Member field is required."})

        # Check if this member already has a pending loan
        if Loan.objects.filter(member=member, status='pending').exists():
            raise ValidationError({
                "detail": f"{member.get_full_name() or member.username} already has a pending loan request."
            })

        serializer.save()

      


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Approve a pending loan.
        Sets disbursed date and due date. Changes status to 'active'.
        """
        loan = self.get_object()

        # Ensure only pending loans can be approved
        if loan.status != 'pending':
            return Response(
                {'detail': 'Only pending loans can be approved.'},
                status=400
            )

        # If created_at is missing for any reason, set it
        if not loan.created_at:
            loan.created_at = now()

        # Set approval details
        loan.status = 'active'
        loan.disbursed_date = now().date()
        loan.due_date = loan.disbursed_date + relativedelta(months=loan.term)

        loan.save()

        return Response(
            {'detail': 'Loan approved successfully.'},
            status=200
        )


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """
        Reject a pending loan.
        """
        loan = self.get_object()
        if loan.status != 'pending':
            return Response({'detail': 'Only pending loans can be rejected.'}, status=400)

        loan.status = 'rejected'
        loan.save()
        return Response({'detail': 'Loan rejected.'}, status=200)
    
    

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def cancel(self, request, pk=None):
        """
        Cancel a loan that is pending or active.
        """
        loan = self.get_object()
        if loan.status not in ['pending', 'active']:
            return Response({'detail': 'Only pending or active loans can be cancelled.'}, status=400)

        loan.status = 'cancelled'
        loan.save()
        return Response({'detail': 'Loan cancelled.'}, status=200)

    
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        """
        Return the active loan for the current user.
        """
        
        user = request.user
        try:
            loan = Loan.objects.get(member=user, status='active')
            serializer = self.get_serializer(loan)
            return Response(serializer.data)
        except Loan.DoesNotExist:
            return Response({"detail": "No active loan found."}, status=status.HTTP_404_NOT_FOUND)
    
    
    
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pending(self, request):
        """
        Return the pendinf loan for the current user.
        """
        
        user = request.user
        try:
            loan = Loan.objects.get(member=user, status='pending')
            serializer = self.get_serializer(loan)
            return Response(serializer.data)
        except Loan.DoesNotExist:
            return Response({"detail": "No pending loan found."}, status=status.HTTP_404_NOT_FOUND)
        
        
        

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def history(self, request):
        """
        Return completed or cancelled loans for the current user.
        """
        user = request.user
        loans = Loan.objects.filter(member=user, status__in=['completed', 'cancelled', 'rejected'])
        serializer = self.get_serializer(loans, many=True)
        return Response(serializer.data)





class LoanRepaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet to manage loan repayments:
    - Add repayments manually (account officer)
    - View repayment history
    """
    queryset = LoanRepayment.objects.all()
    serializer_class = LoanRepaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Members can only see their own loan repayments.
        Staff can see all.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return LoanRepayment.objects.all()
        return LoanRepayment.objects.filter(loan__member=user)
    

    def perform_create(self, serializer):
        """
        Handles creation of repayment entry.
        Automatically assigns the active loan for the given member.
        """
        member_id = self.request.data.get("member")  # Raw ID from frontend
        member = get_object_or_404(CustomUser, id=member_id)  # Get actual instance
       

        # Find active loan for that member
        active_loan = Loan.objects.filter(member=member, status="active").first()
        print(member)
        if not active_loan:
            raise serializers.ValidationError({"loan": "No active loan found for this member."})

        # Save repayment with active loan
        serializer.save(loan=active_loan, member=member)




