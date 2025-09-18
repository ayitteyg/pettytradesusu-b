from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from datetime import datetime
from .models import Transaction  # adjust path if needed





class MemberDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_year = datetime.now().year

        # 1. Total savings (YTD)
        total_savings = Transaction.objects.filter(
            member=user,
            transaction_type='deposit',
            date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 2. Total withdrawals (YTD)
        total_withdrawals = Transaction.objects.filter(
            member=user,
            transaction_type='withdrawal',
            date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 3. Current balance
        credits = Transaction.objects.filter(
            member=user,
            transaction_type__in=['deposit', 'interest_earned']
        ).aggregate(total=Sum('amount'))['total'] or 0

        debits = Transaction.objects.filter(
            member=user,
            transaction_type__in=['withdrawal', 'loan_repayment', 'charges']
        ).aggregate(total=Sum('amount'))['total'] or 0

        current_balance = credits - debits

        # 4. Recent 6 transactions
        recent_transactions = Transaction.objects.filter(member=user).order_by('-date')[:6]
        recent_data = [
            {
                "id": tx.id,
                "date": tx.date,
                "type": tx.transaction_type,
                "amount": float(tx.amount),
                "description": tx.notes
            }
            for tx in recent_transactions
        ]

        # 5. Monthly savings trend for current year
        from django.db.models.functions import ExtractMonth
        savings_by_month = Transaction.objects.filter(
            member=user,
            transaction_type='deposit',
            date__year=current_year
        ).annotate(month=ExtractMonth('date')).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        # Map month number to name
        import calendar
        savings_trend = [
            {
                "month": calendar.month_name[item["month"]],
                "amount": float(item["total"])
            }
            for item in savings_by_month
        ]

        # Final response
        return Response({
            "status": True,
            "data": {
                "summary": {
                    "total_savings": float(total_savings),
                    "total_withdrawals": float(total_withdrawals),
                    "current_balance": float(current_balance),
                },
                "recent_transactions": recent_data,
                "savings_trend": savings_trend,
            }
        })
