from rest_framework import serializers

from .models import ImagingAttachment, ImagingCatalog, ImagingOrder, ImagingReport


class ImagingCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingCatalog
        fields = [
            'id',
            'name',
            'modality',
            'description',
            'preparation',
            'price',
            'turnaround_hours',
            'is_active',
            'created_at',
        ]


class ImagingAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = ImagingAttachment
        fields = [
            'id',
            'order',
            'file_url',
            'file_name',
            'mime_type',
            'size_bytes',
            'metadata_json',
            'uploaded_by',
            'uploaded_by_name',
            'created_at',
        ]
        read_only_fields = ['uploaded_by', 'created_at']


class ImagingReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    released_by_name = serializers.CharField(source='released_by.get_full_name', read_only=True)

    class Meta:
        model = ImagingReport
        fields = [
            'id',
            'order',
            'findings',
            'impression',
            'recommendation',
            'report_status',
            'is_critical',
            'critical_notified_at',
            'reported_by',
            'reported_by_name',
            'released_by',
            'released_by_name',
            'released_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'reported_by',
            'critical_notified_at',
            'released_by',
            'released_at',
            'created_at',
            'updated_at',
        ]


class ImagingOrderSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    catalog_name = serializers.CharField(source='catalog_item.name', read_only=True)
    modality = serializers.CharField(source='catalog_item.modality', read_only=True)
    assigned_radiologist_name = serializers.CharField(source='assigned_radiologist.user.get_full_name', read_only=True)
    report = ImagingReportSerializer(read_only=True)

    class Meta:
        model = ImagingOrder
        fields = [
            'id',
            'patient',
            'patient_name',
            'catalog_item',
            'catalog_name',
            'modality',
            'ordered_by',
            'assigned_radiologist',
            'assigned_radiologist_name',
            'priority',
            'status',
            'clinical_notes',
            'scheduled_at',
            'started_at',
            'completed_at',
            'released_at',
            'created_at',
            'updated_at',
            'report',
        ]
        read_only_fields = ['ordered_by', 'released_at', 'created_at', 'updated_at']
