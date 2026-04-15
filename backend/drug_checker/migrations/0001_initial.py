# Generated manually for phase 3 bootstrap

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DrugInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('drug_a', models.CharField(max_length=200)),
                ('drug_b', models.CharField(max_length=200)),
                ('drug_a_normalized', models.CharField(db_index=True, max_length=200)),
                ('drug_b_normalized', models.CharField(db_index=True, max_length=200)),
                ('severity', models.CharField(choices=[('MINOR', 'Minor'), ('MODERATE', 'Moderate'), ('MAJOR', 'Major'), ('CONTRAINDICATED', 'Contraindicated')], default='MODERATE', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('management', models.TextField(blank=True)),
                ('source', models.CharField(blank=True, max_length=120)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('drug_a_normalized', 'drug_b_normalized')},
            },
        ),
        migrations.CreateModel(
            name='InteractionCheckLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medicines', models.JSONField(default=list)),
                ('interactions_found', models.PositiveIntegerField(default=0)),
                ('worst_severity', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('checked_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drug_interaction_checks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='druginteraction',
            index=models.Index(fields=['drug_a_normalized', 'drug_b_normalized'], name='drug_checker_drug_a__d0cf5d_idx'),
        ),
        migrations.AddIndex(
            model_name='druginteraction',
            index=models.Index(fields=['severity'], name='drug_checker_severit_420f65_idx'),
        ),
    ]
