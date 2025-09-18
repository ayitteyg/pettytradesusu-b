from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model


def get_today():
    return timezone.now().date()



"""
Credit Union Management App Models
Designed to support multiple churches and detailed member profiles.


# Delete migration files
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Delete SQLite database (if using SQLite)
rm db.sqlite3

"""

class Church(models.Model):
    """
    Represents a Church in the system.
    Multiple members can belong to a church.
    """
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.name



class CustomUser(AbstractUser):
    """
    Extends Django's default User to include roles and church association.
    """
    is_member = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_officer = models.BooleanField(default=False)
    church = models.ForeignKey(Church, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.username



class Member(models.Model):
    """
    Represents a detailed profile for each church member.
    Linked to the user account.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='member')
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    membership_number = models.CharField(max_length=50, unique=True)
    join_date = models.DateField(auto_now_add=True)
    occupation = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.full_name




class Saving(models.Model):
    """
    Tracks savings (contributions) made by members.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='savings_recorded')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Savings by {self.user.username} on {self.date}"




class Loan(models.Model):
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='loans')
    """
    Represents a loan request and its lifecycle.
    Tracks principal, interest, total repayment, and loan status.
    """

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )


    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='loans')
    
    
    account_officer  = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_loan',
        help_text="The account officer who recorded the loan request"
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Principal amount")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate (%)")
    term = models.PositiveIntegerField(help_text="Loan term in months")
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total amount to repay (Principal + Interest)"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    disbursed_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True, help_text="Expected end date of repayment")
    
    created_at = models.DateField(auto_now_add=True)
    purpose = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan {self.id} - {self.member.username} - {self.status}"

    def calculate_due_date(self):
        """
        Calculates and sets the due date based on disbursement and term.
        """
        if self.disbursed_date and self.term:
            self.due_date = self.disbursed_date + relativedelta(months=self.term)

    def total_repaid(self):
        """
        Returns the total repaid amount for this loan.
        """
        return sum(r.amount_paid for r in self.repayments.all())

    def balance_remaining(self):
        """
        Returns the remaining balance on the loan.
        """
        return max(self.total_amount - self.total_repaid(), 0)

    def is_fully_paid(self):
        """
        Returns True if loan is fully repaid.
        """
        return self.total_repaid() >= self.total_amount

    def __str__(self):
        return f"Loan {self.id} - {self.member.username}"
    


class LoanRepayment(models.Model):
    """
    Represents a repayment made toward a specific loan.
    Linked to one active loan at a time.
    Can be added manually by an account officer or automatically via MoMo.
    """

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=get_today)
    

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-payment_date']
    def __str__(self):
        return f"Repayment of {self.amount_paid} by {self.member.username} on {self.payment_date}"



class Transaction(models.Model):
    """
    Logs all financial transactions: deposits, withdrawals, and loan repayments.

    - `member`: the user for whom the transaction is made (the account owner).
    - `recorded_by`: the user who recorded the transaction (account officer).
    """
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('loan_repayment', 'Loan Repayment'),
        ('charges', 'Charges'),
        ('interest_earned', 'Interest Earned')
    ]

    member = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='member_transactions',
        help_text="The user who made the transaction"
        
    )
    account_officer  = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_transactions',
        help_text="The account officer who recorded the transaction"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.member.username} - {self.amount}"



class Notification(models.Model):
    """
    Sends alerts and messages to users about transactions, approvals, and reminders.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"

