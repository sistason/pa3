# Generated by Django 2.0.4 on 2018-04-13 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pa3_web', '0002_subscriber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriber',
            name='src',
            field=models.CharField(choices=[(['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11'], ['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11']), (['H 10'], ['H 10']), (['H 19', 'H 23', 'H 25'], ['H 19', 'H 23', 'H 25']), (['H 02'], ['H 02'])], max_length=50),
        ),
    ]
