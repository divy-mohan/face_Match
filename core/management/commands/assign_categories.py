from django.core.management.base import BaseCommand
from core.models import Supervisor, JobCategory


class Command(BaseCommand):
    help = 'Assign job categories to supervisors'

    def add_arguments(self, parser):
        parser.add_argument('supervisor_id', type=int, help='Supervisor ID')
        parser.add_argument('category_ids', nargs='+', type=int, help='Category IDs to assign')

    def handle(self, *args, **options):
        try:
            supervisor = Supervisor.objects.get(id=options['supervisor_id'])
            categories = JobCategory.objects.filter(id__in=options['category_ids'])
            
            supervisor.assigned_categories.set(categories)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned {categories.count()} categories to {supervisor.full_name}'
                )
            )
            
            for category in categories:
                self.stdout.write(f'  - {category.name}')
                
        except Supervisor.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Supervisor with ID {options["supervisor_id"]} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )