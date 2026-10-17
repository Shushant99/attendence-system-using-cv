from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_teacher_assigned_classrooms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='photo',
            field=models.ImageField(blank=True, upload_to='student_photos/'),
        ),
    ]
