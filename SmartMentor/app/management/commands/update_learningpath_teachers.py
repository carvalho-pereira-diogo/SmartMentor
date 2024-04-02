from django.core.management.base import BaseCommand
from app.models import Teacher, LearningPath

class Command(BaseCommand):
    help = 'Updates the teacher field in all LearningPath instances'

    def handle(self, *args, **options):
        # Get the first Teacher instance
        teacher = Teacher.objects.first()

        if not teacher:
            self.stdout.write(self.style.ERROR('No Teacher instances found.'))
            return

        # Update the teacher field in all LearningPath instances
        LearningPath.objects.update(teacher=teacher)

        self.stdout.write(self.style.SUCCESS('Successfully updated teacher field in all LearningPath instances.'))