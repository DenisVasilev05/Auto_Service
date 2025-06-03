from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.db import transaction
from django.core.management.base import CommandError
from service.models import Facility, create_facility_schedule

class Command(BaseCommand):
    """Load initial data with signals disabled.
    
    This command temporarily disconnects the Facility post_save signal
    to prevent duplicate Schedule creation when loading fixture data.
    It also sets up known passwords for all users.
    """

    def handle(self, *args, **options):
        # Define initial passwords for all users
        user_passwords = {
            'admin': 'admin123',
            'owner': 'owner123',
            'customer1': 'customer123'
        }

        # Disconnect the signal
        post_save.disconnect(create_facility_schedule, sender=Facility)

        try:
            with transaction.atomic():
                try:
                    # Load the fixture data
                    call_command('loaddata', 'service/fixtures/populate.json', verbosity=1)
                except Exception as e:
                    raise CommandError(f'Failed to load fixture data: {str(e)}')
                
                # Set known passwords for all users
                missing_users = []
                for username, password in user_passwords.items():
                    try:
                        user = User.objects.get(username=username)
                        user.set_password(password)
                        user.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'Password for {username} set to: {password}')
                        )
                    except User.DoesNotExist:
                        missing_users.append(username)
                
                if missing_users:
                    self.stdout.write(
                        self.style.WARNING(
                            f'The following users were not found in fixture data: {", ".join(missing_users)}'
                        )
                    )
                
                self.stdout.write(self.style.SUCCESS('Successfully loaded initial data'))
        
        except CommandError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An unexpected error occurred: {str(e)}')
            )
            raise
        finally:
            # Reconnect the signal
            post_save.connect(create_facility_schedule, sender=Facility) 