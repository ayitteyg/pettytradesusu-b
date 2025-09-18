from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import ROUND_HALF_UP, Decimal, getcontext, InvalidOperation

from .models import Loan, LoanRepayment, Member
from datetime import date
from django.db import models
from dateutil.relativedelta import relativedelta 
from .serializers import LoanListSerializer









@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_summary(request):
    user = request.user
    
    print(user)
    
    
    member = getattr(user, 'member', None)  # adjust if you use a related profile
    print(f"user: {request.user}, type: {type(request.user)}")  # Should be CustomUser
    print(f"member: {member}, type: {type(member)}")  # Should be Member
    print(f"member.user: {member.user}, type: {type(member.user)}")  # Should be CustomUser

    if not member:
        return Response({"detail": "Member profile not found."}, status=400)
    
   
    # Get active loan
    if not isinstance(member, Member):
        return Response({"detail": "Invalid member instance."}, status=400)
    
    active_loan = Loan.objects.filter(member=member.user, status='active').first()
    active_loan_data = None

    
    
    if active_loan:
        total_repayment = active_loan.total_amount
        paid_amount = LoanRepayment.objects.filter(loan=active_loan).aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        
        getcontext().prec = 2  # set precision if needed
        
        # term_years = Decimal(active_loan.term) / Decimal(12)
        # total_amount = active_loan.amount * (Decimal(1) + active_loan.interest_rate) 
        # total_amount = float(total_amount) 
        
        
        term_years = Decimal(active_loan.term) / Decimal(12)
        total_amount = active_loan.amount + (active_loan.amount * (active_loan.interest_rate/100) * term_years) 
        total_amount = float(total_amount)  
        
        print(active_loan.amount, active_loan.interest_rate, term_years, active_loan.term )
        

        try:
            # Ensure numeric values are properly converted to Decimal
            total_repayment = Decimal(str(total_repayment))
            term = Decimal(active_loan.term)
            
            if term <= 0:
                monthly_amount = Decimal('0')
            else:
                monthly_amount = total_repayment / term
            
            paid_installments = int(paid_amount / monthly_amount) if monthly_amount else 0
            next_installment_number = paid_installments + 1

            if next_installment_number <= active_loan.term:
                next_payment_date = active_loan.created_at + relativedelta(months=+next_installment_number)
                try:
                    quantized_amount = float(monthly_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    next_payment = {
                        "date": next_payment_date.strftime("%Y-%m-%d"),
                        "amount": quantized_amount
                    }
                except InvalidOperation:
                    next_payment = {
                        "date": next_payment_date.strftime("%Y-%m-%d"),
                        "amount": float(monthly_amount)
                    }
            else:
                next_payment = None  # fully paid

        except (InvalidOperation, TypeError, ValueError) as e:
            # Log the error for debugging
            print(f"Error calculating payment: {e}")
            next_payment = None
            
    

        active_loan_data = {
            "id": f"LN-{active_loan.created_at.year}-{active_loan.id:04}",
            "amount": float(active_loan.amount),
            "disbursedDate": active_loan.created_at.strftime("%Y-%m-%d"),
            "term": active_loan.term,
            "interestRate": float(active_loan.interest_rate),
            'totalAmount' : float(total_amount), #compound
            "totalRepayments": float(paid_amount),
            "paidAmount": float(paid_amount),
            "nextPayment": next_payment
        }


    # Get loan history (completed loans)
    history_qs = Loan.objects.filter( member=member.user, status__in=['active', 'completed'] ).order_by('-created_at')
    loan_history = []

    for loan in history_qs:
        total_paid = LoanRepayment.objects.filter(loan=loan).aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')

        interest_paid = total_paid - loan.amount

        loan_history.append({
            "id": f"LN-{loan.created_at.year}-{loan.id:04}",
            "principal": float(loan.amount),
            "interestPaid": float(interest_paid),
            "totalPayment": float(total_paid),
            "status": loan.status,
            "dateClosed": loan.due_date.strftime("%Y-%m-%d")
        })

    return Response({
        "activeLoan": active_loan_data,
        "loanHistory": loan_history
    })




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loan_history_view(request):
    """
    Return loan history with fields: date, amount, and status.
    This is a simplified version for frontend display.
    """
    user = request.user
    member = getattr(user, 'member', None)

    if not member:
        return Response({"detail": "Member profile not found."}, status=400)

    loans = Loan.objects.filter(member=member.user).order_by('-created_at')

    history = [
        {
            "date": loan.created_at,
            "amount": float(loan.amount),
            "status": loan.status
        }
        for loan in loans
    ]

    return Response(history)




@api_view(['GET'])
def loan_list(request):
    """
    Returns all loans with statuses active, pending, or rejected.
    """
    loans = Loan.objects.filter(status__in=['active', 'pending', 'rejected']).select_related('member')
    serializer = LoanListSerializer(loans, many=True)
    return Response(serializer.data)