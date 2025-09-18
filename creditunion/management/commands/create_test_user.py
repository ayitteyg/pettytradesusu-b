from django.core.management.base import BaseCommand
from creditunion.models import CustomUser, Church, Member
import uuid

class Command(BaseCommand):
    help = 'Create a test user for login authentication testing.'

    def handle(self, *args, **kwargs):
        # Create or get a test church
        church, _ = Church.objects.get_or_create(name='Church1')

        # Create test user
        user, created = CustomUser.objects.get_or_create(
            username='testuser',
            defaults={
                'is_member': True,
                'is_admin': False,
                'church': church,
                'phone': '0540000000',
                
            }
        )

        # Set or update password
        user.set_password('password123')
        user.save()

        if created:
            # Create member profile
            Member.objects.create(
                user=user,
                full_name='TestUser',
                membership_number=f"CU-{uuid.uuid4().hex[:6].upper()}",
                occupation='Tester'
            )
            self.stdout.write(self.style.SUCCESS('✅ Test user "testuser" created with password "password123".'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Test user already exists. Password was updated.'))
