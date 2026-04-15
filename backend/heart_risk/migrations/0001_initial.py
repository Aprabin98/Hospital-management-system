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
            name='HeartRiskAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age', models.PositiveSmallIntegerField()),
                ('sex', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('systolic_bp', models.PositiveSmallIntegerField()),
                ('diastolic_bp', models.PositiveSmallIntegerField()),
                ('total_cholesterol', models.PositiveSmallIntegerField(help_text='mg/dL')),
                ('fasting_blood_sugar', models.PositiveSmallIntegerField(help_text='mg/dL')),
                ('bmi', models.DecimalField(decimal_places=2, max_digits=5)),
                ('smoker', models.BooleanField(default=False)),
                ('diabetic', models.BooleanField(default=False)),
                ('family_history', models.BooleanField(default=False)),
                ('chest_pain', models.BooleanField(default=False)),
                ('sedentary_lifestyle', models.BooleanField(default=False)),
                ('risk_score', models.PositiveSmallIntegerField()),
                ('risk_level', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')], max_length=10)),
                ('summary', models.TextField(blank=True)),
                ('recommendations', models.TextField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assessed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='heart_risk_assessments', to=settings.AUTH_USER_MODEL)),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='heart_risk_assessments', to='clinical.doctor')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='heart_risk_assessments', to='users.patientprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='heartriskassessment',
            index=models.Index(fields=['patient', 'created_at'], name='heart_risk__patient_7047c1_idx'),
        ),
        migrations.AddIndex(
            model_name='heartriskassessment',
            index=models.Index(fields=['risk_level'], name='heart_risk__risk_le_151f15_idx'),
        ),
    ]
