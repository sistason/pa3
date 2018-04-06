# Generated by Django 2.0.3 on 2018-03-23 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NewestNumberBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src', models.CharField(choices=[('pa_23', 'Hpa_23: H 19, H 23, H 25'), ('pa_10', 'Hpa_10: H 10'), ('pa_13', 'Hpa_13: Schalter 1/2, Schalter 3/4, Schalter 5/6, Schalter 7/8/9, Schalter 10/11'), ('pa_02', 'Hpa_02: H 02')], max_length=50)),
                ('date', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='StatisticalData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src', models.CharField(choices=[(['H 19', 'H 23', 'H 25'], ['H 19', 'H 23', 'H 25']), (['H 10'], ['H 10']), (['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11'], ['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11']), (['H 02'], ['H 02'])], max_length=50)),
                ('date', models.IntegerField()),
                ('avg', models.FloatField()),
                ('avg_len', models.IntegerField()),
                ('avg_sum', models.IntegerField()),
                ('avg_proc_delay_sum', models.IntegerField(null=True)),
                ('avg_proc_delay_len', models.IntegerField(null=True)),
                ('avg_last_two_weeks', models.FloatField()),
                ('avg_last_same_day', models.FloatField()),
                ('avg_whole', models.FloatField()),
                ('avg_proc_delay_whole', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='WaitingNumber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src', models.CharField(choices=[(['H 19', 'H 23', 'H 25'], ['H 19', 'H 23', 'H 25']), (['H 10'], ['H 10']), (['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11'], ['Schalter 1/2', 'Schalter 3/4', 'Schalter 5/6', 'Schalter 7/8/9', 'Schalter 10/11']), (['H 02'], ['H 02'])], max_length=50)),
                ('date', models.IntegerField()),
                ('date_delta', models.IntegerField(null=True)),
                ('proc_delay', models.FloatField(null=True)),
                ('number', models.SmallIntegerField()),
                ('statistic', models.ForeignKey(on_delete=None, to='pa3.StatisticalData')),
            ],
            options={
                'ordering': ['-date', 'src'],
            },
        ),
        migrations.CreateModel(
            name='WaitingNumberBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src', models.CharField(choices=[('pa_23', 'Hpa_23: H 19, H 23, H 25'), ('pa_10', 'Hpa_10: H 10'), ('pa_13', 'Hpa_13: Schalter 1/2, Schalter 3/4, Schalter 5/6, Schalter 7/8/9, Schalter 10/11'), ('pa_02', 'Hpa_02: H 02')], db_index=True, max_length=50)),
                ('src_ip', models.GenericIPAddressField()),
                ('date', models.IntegerField(db_index=True)),
                ('date_delta', models.IntegerField(null=True)),
                ('proc_delay', models.FloatField(null=True)),
                ('numbers', models.ManyToManyField(to='pa3.WaitingNumber')),
            ],
            options={
                'ordering': ['-date', 'src'],
            },
        ),
        migrations.AddField(
            model_name='newestnumberbatch',
            name='newest',
            field=models.ForeignKey(on_delete=None, to='pa3.WaitingNumberBatch'),
        ),
    ]
