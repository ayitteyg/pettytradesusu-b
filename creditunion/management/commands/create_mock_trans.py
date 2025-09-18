import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware

from creditunion.models import Transaction

User = get_user_model()

class Command(BaseCommand):
    help = "Seed mock transaction data for a test member and account officer."

    def handle(self, *args, **kwargs):
        """
        This command:
        - Creates two test users: one as a `member` and the other as an `account officer`.
        - Clears old transactions for the member.
        - Seeds random mock transactions (deposit, withdrawal, etc.) tied to the member,
          and tracked as entered by the account officer.
        Useful for dashboard testing.
        """

        # Create member user
        member_username = "testmember1"
        member, created_member = User.objects.get_or_create(username=member_username, defaults={
            'email': f"{member_username}@mail.com",
            'is_member': True,
        })
        if created_member:
            member.set_password("memberpass123")
            member.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created test member '{member_username}'"))
        else:
            self.stdout.write(f"ℹ️  Using existing test member '{member_username}'")

        # Create account officer user
        officer_username = "testofficer1"
        officer, created_officer = User.objects.get_or_create(username=officer_username, defaults={
            'email': f"{officer_username}@mail.com",
            'is_officer': True,
        })
        if created_officer:
            officer.set_password("officerpass123")
            officer.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created test officer '{officer_username}'"))
        else:
            self.stdout.write(f"ℹ️  Using existing test officer '{officer_username}'")

        # Delete old transactions for the member
        Transaction.objects.filter(member=member).delete()
        self.stdout.write("🧹 Cleared existing transactions for member.")

        # Generate mock transactions
        transaction_types = ['deposit', 'withdrawal', 'charges', 'interest_earned']
        start_date = datetime(datetime.now().year, 1, 1)

        for _ in range(100):
            tx_type = random.choices(
                transaction_types,
                weights=[0.5, 0.3, 0.1, 0.1],  # Higher probability for deposits
                k=1
            )[0]

            amount = round(random.uniform(20, 1500), 2)
            tx_date = make_aware(start_date + timedelta(days=random.randint(0, 210)))

            Transaction.objects.create(
                member=member,
                account_officer=officer,
                transaction_type=tx_type,
                amount=amount,
                date=tx_date,
                reference=f"TXN{random.randint(100000, 999999)}",
                notes=f"Mock {tx_type} entry"
            )

        self.stdout.write(self.style.SUCCESS("✅ 100 mock transactions created successfully."))
