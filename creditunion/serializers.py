from decimal import Decimal
from rest_framework import serializers
from .models import Transaction
from .models import CustomUser, Loan, LoanRepayment, Member, Church
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models  # Add this line
from datetime import datetime
import os


User = get_user_model()

def get_today():
    return timezone.now().date()


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model.
    Accepts both the member (user initiating the transaction) and
    the account officer (user recording it).
    """
    class Meta:
        model = Transaction
        fields = [
            'id', 'member', 'account_officer',
            'transaction_type', 'amount',
            'date', 'reference', 'notes'
        ]
        read_only_fields = ['account_officer']
        
        

    def create(self, validated_data):
        """
        Overridden to set the account officer from request context automatically.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['account_officer'] = request.user
        return super().create(validated_data)



class MemberSerializer(serializers.ModelSerializer):
    """Serializer for listing members in dropdowns."""
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email']



class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'
        read_only_fields = ['status', 'total_amount', 'disbursed_date', 'due_date', 'created_at']

    def create(self, validated_data):
        """
        Automatically attach the current user as the loan applicant.
        Set initial status to 'pending'. Calculate total_amount based on principal, interest, and term.
        """
         # user = self.context['request'].user
        # validated_data['member'] = user
        validated_data['status'] = 'pending'
        
        principal = validated_data['amount']
        rate = validated_data['interest_rate'] / Decimal('100')  # Convert to a proper decimal percentage
        term = Decimal(validated_data['term'])

        # Simple interest formula: Interest = P * R * T
        interest = principal * rate * (term / Decimal('12'))
        validated_data['total_amount'] = principal + interest

        

        return super().create(validated_data)
    
    

class LoanRepaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for recording loan repayments.

    Automatically validates:
    - Member has an active loan.
    - Loan status is 'active'.
    - Prevents repayment to non-active loans.

    Handles:
    - Updating total repaid.
    - Automatically marking loan as completed if fully paid.
    """

    loan_id = serializers.IntegerField(write_only=True, required=False)  # <-- not required
    payment_date = serializers.SerializerMethodField()
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())  # or User.objects.all()

    class Meta:
        model = LoanRepayment
        fields = ['id', 'loan_id', 'amount_paid', 'payment_date', 'member']

    def get_payment_date(self, obj):
        """
        Ensure we only return a date, not a datetime.
        """
        if isinstance(obj.payment_date, datetime):
            return obj.payment_date.date()
        return obj.payment_date


    def create(self, validated_data):
        member = validated_data['member']
        amount_paid = validated_data['amount_paid']

        # Find active loan
        loan = Loan.objects.filter(member=member, status='active').first()
        if not loan:
            raise serializers.ValidationError("No active loan found for this member.")

        repayment = LoanRepayment.objects.create(
            loan=loan,
            amount_paid=amount_paid,
            member=loan.member,  # ✅ ensure member is set
            payment_date=timezone.now().date(),
        )

        # Update loan status if fully paid
        total_paid = loan.repayments.aggregate(total=models.Sum('amount_paid'))['total'] or Decimal('0.00')
        if total_paid >= loan.total_amount:
            loan.status = 'completed'
            loan.save()

        return repayment


class LoanListSerializer(serializers.ModelSerializer):
    memberUuid = serializers.CharField(source='member.member.membership_number')
    memberName = serializers.CharField(source='member.member.full_name')
    requestDate = serializers.DateField(source='created_at', format='%Y-%m-%d')
    disbursed_date = serializers.DateField()
    due_date = serializers.DateField()

    class Meta:
        model = Loan
        fields = [
            'id',
            'requestDate',
            'memberUuid',
            'memberName',
            'amount',
            'purpose',
            'status',
            'due_date',
            'disbursed_date',
            
        ]
        
        read_only_fields = [
            'due_date',
            'disbursed_date',
            ]
        


class MemberProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for fetching and updating a member's profile,
    combining fields from CustomUser and Member models.
    Deletes old profile picture if replaced.
    """
    
    membership_number = serializers.CharField(source='member.membership_number', read_only=True)

    
    church = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser._meta.get_field('church').related_model.objects.all(),
        required=False
    )
    phone = serializers.CharField(source='user.phone', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Member
        fields = [
            'full_name',
            'date_of_birth',
            'occupation',
            'profile_picture',
            'church',
            'phone',
            'email',
            "membership_number",  # ✅ added
        ]

    def update(self, instance, validated_data):
        # Extract user-related fields
        user_data = validated_data.pop('user', {})
        
        # Update CustomUser fields
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        if 'church' in validated_data:
            user.church = validated_data.pop('church')
        user.save()

        # Handle profile picture replacement
        new_picture = validated_data.get('profile_picture', None)
        if new_picture and instance.profile_picture:
            old_path = instance.profile_picture.path
            if os.path.exists(old_path):
                os.remove(old_path)

        # Update Member fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance



class ChurchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Church
        fields = "__all__"