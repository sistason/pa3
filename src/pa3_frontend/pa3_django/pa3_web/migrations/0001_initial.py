# Generated by Django 2.0.2 on 2018-02-26 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src', models.CharField(choices=[('FR', 'FR'), ('PA', 'PA')], max_length=2)),
                ('date', models.IntegerField()),
                ('news', models.TextField()),
                ('last_checked', models.IntegerField()),
            ],
        ),
    ]
