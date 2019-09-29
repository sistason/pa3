# Generated by Django 2.0.4 on 2018-04-13 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pa3', '0005_auto_20180413_0835'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newestnumberbatch',
            name='src',
            field=models.CharField(choices=[('pa_13', 'H 13'), ('pa_10', 'H 10'), ('pa_23', 'H 23'), ('pa_02', 'H 02')], max_length=50),
        ),
        migrations.AlterField(
            model_name='statisticaldata',
            name='src',
            field=models.CharField(choices=[(['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11'], ['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11']), (['H 10'], ['H 10']), (['H 19', 'H 23', 'H 25'], ['H 19', 'H 23', 'H 25']), (['H 02'], ['H 02'])], max_length=50),
        ),
        migrations.AlterField(
            model_name='waitingnumber',
            name='src',
            field=models.CharField(choices=[(['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11'], ['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11']), (['H 10'], ['H 10']), (['H 19', 'H 23', 'H 25'], ['H 19', 'H 23', 'H 25']), (['H 02'], ['H 02'])], max_length=50),
        ),
        migrations.AlterField(
            model_name='waitingnumberbatch',
            name='src',
            field=models.CharField(choices=[('pa_13', 'H 13'), ('pa_10', 'H 10'), ('pa_23', 'H 23'), ('pa_02', 'H 02')], db_index=True, max_length=50),
        ),
    ]
