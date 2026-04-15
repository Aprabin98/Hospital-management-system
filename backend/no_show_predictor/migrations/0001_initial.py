from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clinical', '0001_initial'),
        ('users', '0005_twofactorcode'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NoShowPredictionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_date', models.DateField()),
                ('risk_score', models.PositiveSmallIntegerField()),
                ('risk_level', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], max_length=10)),
                ('factors', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='no_show_prediction_logs', to=settings.AUTH_USER_MODEL)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='no_show_predictions', to='clinical.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='no_show_predictions', to='users.patientprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='noshowpredictionlog',
            index=models.Index(fields=['patient', 'appointment_date'], name='no_show_pre_patient_e5ff4a_idx'),
        ),
        migrations.AddIndex(
            model_name='noshowpredictionlog',
            index=models.Index(fields=['doctor', 'appointment_date'], name='no_show_pre_doctor__840958_idx'),
        ),
        migrations.AddIndex(
            model_name='noshowpredictionlog',
            index=models.Index(fields=['risk_level'], name='no_show_pre_risk_le_118977_idx'),
        ),
    ]
