# Generated by Django 4.0.1 on 2022-07-28 13:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0002_remove_course_coordinators_course_coordinators'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='course',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Users.course'),
            preserve_default=False,
        ),
    ]
