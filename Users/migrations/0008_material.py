# Generated by Django 4.0.1 on 2022-07-29 16:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0007_announcement'),
    ]

    operations = [
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('material', models.FileField(upload_to='course_materials')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Users.course')),
            ],
        ),
    ]