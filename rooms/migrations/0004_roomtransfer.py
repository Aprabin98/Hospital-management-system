# Generated migration for RoomTransfer model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('clinical', '0001_initial'),
        ('rooms', '0003_admissionrequest_preferred_room_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoomTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=255)),
                ('status', models.CharField(
                    choices=[('PENDING', 'Pending Confirmation'), ('APPROVED', 'Approved'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')],
                    default='PENDING',
                    max_length=15,
                )),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('doctor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_transfers', to='clinical.doctor')),
                ('from_bed', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transfers_from', to='rooms.roombed')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_transfers', to='users.patientprofile')),
                ('to_bed', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transfers_to', to='rooms.roombed')),
            ],
            options={
                'ordering': ['-requested_at'],
            },
        ),
    ]
