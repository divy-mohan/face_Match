# Generated manually for assigned_categories field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_supervisor_assigned_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='supervisor',
            name='assigned_categories',
            field=models.ManyToManyField(blank=True, to='core.jobcategory'),
        ),
    ]