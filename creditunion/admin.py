from django.contrib import admin
from .models import CustomUser, Loan, Transaction

# Register your models here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    pass



@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for Loan model.
    Provides list display, filtering, and search functionality.
    """
    list_display = (
        "id",
        "member",
        "account_officer",
        "amount",
        "interest_rate",
        "term",
        "total_amount",
        "status",
        "disbursed_date",
        "due_date",
        "created_at",
    )

    list_filter = (
        "status",
        "disbursed_date",
        "due_date",
        "created_at",
    )

    search_fields = (
        "member__username",
        "member__email",
        "account_officer__username",
        "account_officer__email",
        "purpose",
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"




@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for Transaction model.
    Provides useful list display, filtering, and search features.
    """
    list_display = (
        "id",
        "transaction_type",
        "member",
        "account_officer",
        "amount",
        "date",
        "reference",
    )

    list_filter = (
        "transaction_type",
        "date",
    )

    search_fields = (
        "member__username",
        "member__email",
        "account_officer__username",
        "account_officer__email",
        "reference",
        "notes",
    )

    ordering = ("-date",)
    date_hierarchy = "date"
    
    
    