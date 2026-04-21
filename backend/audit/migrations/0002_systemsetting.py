from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hospital_name', models.CharField(default='Hospital Management System', max_length=255)),
                ('hospital_email', models.EmailField(default='admin@hospital.com', max_length=254)),
                ('hospital_phone', models.CharField(default='+91-XXXXXXXXXX', max_length=64)),
                ('hospital_address', models.TextField(default='123 Medical Street, City')),
                ('max_appointments_per_day', models.PositiveIntegerField(default=50)),
                ('appointment_slot_duration', models.PositiveIntegerField(default=30)),
                ('cancellation_notice_hours', models.PositiveIntegerField(default=2)),
                ('max_concurrent_users', models.PositiveIntegerField(default=100)),
                ('maintenance_mode', models.BooleanField(default=False)),
                ('auto_backup_enabled', models.BooleanField(default=True)),
                ('backup_frequency_days', models.PositiveIntegerField(default=1)),
                ('enable_two_factor', models.BooleanField(default=True)),
                ('enable_notifications', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_settings_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'System Setting',
                'verbose_name_plural': 'System Settings',
            },
        ),
    ]
