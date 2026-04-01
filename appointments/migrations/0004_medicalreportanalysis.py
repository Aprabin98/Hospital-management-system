from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('appointments', '0003_triageassessment'),
    ]

    operations = [
        migrations.CreateModel(
            name='MedicalReportAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=120)),
                ('report_file', models.FileField(upload_to='appointments/reports/')),
                ('report_type', models.CharField(choices=[('GENERAL', 'General Report'), ('CBC', 'CBC'), ('LIPID', 'Lipid Profile'), ('LIVER', 'Liver Function'), ('RENAL', 'Renal Function'), ('THYROID', 'Thyroid Panel'), ('DIABETES', 'Diabetes Panel')], default='GENERAL', max_length=20)),
                ('extracted_text', models.TextField(blank=True)),
                ('ai_summary', models.TextField(blank=True)),
                ('abnormal_flags', models.JSONField(blank=True, default=list)),
                ('recommendations', models.TextField(blank=True)),
                ('risk_level', models.CharField(choices=[('LOW', 'Low'), ('MODERATE', 'Moderate'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], default='LOW', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_report_analyses', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_analyses', to='users.patientprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
