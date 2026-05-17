# Generated for patient management clinical visit timeline.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinical', '0002_doctorleave_approval_fields'),
        ('users', '0012_patientallergy'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symptoms', models.TextField()),
                ('vitals', models.JSONField(blank=True, default=dict)),
                ('diagnosis', models.TextField(blank=True)),
                ('doctor_notes', models.TextField(blank=True)),
                ('prescribed_medicines', models.TextField(blank=True)),
                ('suggested_tests', models.TextField(blank=True)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('ai_possible_causes', models.TextField(blank=True)),
                ('ai_recommended_tests', models.TextField(blank=True)),
                ('ai_risk_level', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], default='LOW', max_length=10)),
                ('ai_red_flags', models.TextField(blank=True)),
                ('ai_summary', models.TextField(blank=True)),
                ('visit_date', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_patient_visits', to=settings.AUTH_USER_MODEL)),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_visits', to='clinical.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visits', to='users.patientprofile')),
            ],
            options={
                'ordering': ['-visit_date'],
                'indexes': [
                    models.Index(fields=['patient', '-visit_date'], name='clinical_pa_patient_efc0d3_idx'),
                    models.Index(fields=['follow_up_date'], name='clinical_pa_follow__858a55_idx'),
                    models.Index(fields=['ai_risk_level'], name='clinical_pa_ai_risk_587e49_idx'),
                ],
            },
        ),
    ]
