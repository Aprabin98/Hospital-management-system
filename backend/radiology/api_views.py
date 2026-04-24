from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import PatientProfile

from .api_serializers import (
    ImagingAttachmentSerializer,
    ImagingCatalogSerializer,
    ImagingOrderSerializer,
    ImagingReportSerializer,
)
from .models import ImagingAttachment, ImagingCatalog, ImagingOrder, ImagingReport


_ALLOWED_STAFF_ROLES = {
    'ADMIN',
    'DOCTOR',
    'NURSE',
    'RECEPTIONIST',
    'LAB_TECHNICIAN',
}

_REPORTING_ROLES = {
    'ADMIN',
    'DOCTOR',
    'LAB_TECHNICIAN',
}


def _is_patient(user):
    return user.is_authenticated and user.role == 'PATIENT'


def _is_staff(user):
    return user.is_authenticated and user.role in _ALLOWED_STAFF_ROLES


def _can_report(user):
    return user.is_authenticated and user.role in _REPORTING_ROLES


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def imaging_catalog_list_create_api(request):
    if request.method == 'GET':
        queryset = ImagingCatalog.objects.filter(is_active=True)
        serializer = ImagingCatalogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.user.role != 'ADMIN':
        return Response({'detail': 'Only admin can create catalog items.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ImagingCatalogSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def imaging_orders_list_create_api(request):
    if request.method == 'GET':
        if _is_patient(request.user):
            try:
                patient = PatientProfile.objects.get(user=request.user)
            except PatientProfile.DoesNotExist:
                return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            queryset = ImagingOrder.objects.filter(patient=patient)
        elif _is_staff(request.user):
            queryset = ImagingOrder.objects.all()
        else:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        queryset = queryset.select_related('patient__user', 'catalog_item', 'assigned_radiologist__user').prefetch_related('attachments')
        serializer = ImagingOrderSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if not _is_staff(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ImagingOrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(ordered_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def imaging_order_detail_api(request, order_id):
    try:
        order = ImagingOrder.objects.select_related(
            'patient__user',
            'catalog_item',
            'assigned_radiologist__user',
        ).get(pk=order_id)
    except ImagingOrder.DoesNotExist:
        return Response({'detail': 'Imaging order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if _is_patient(request.user):
        if order.patient.user_id != request.user.id:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method != 'GET':
            return Response({'detail': 'Patients cannot modify imaging orders.'}, status=status.HTTP_403_FORBIDDEN)
    elif not _is_staff(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = ImagingOrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = ImagingOrderSerializer(order, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    updated = serializer.save()

    if updated.status == 'IN_PROGRESS' and not updated.started_at:
        updated.started_at = timezone.now()
        updated.save(update_fields=['started_at'])
    if updated.status == 'REPORTED' and not updated.completed_at:
        updated.completed_at = timezone.now()
        updated.save(update_fields=['completed_at'])

    return Response(ImagingOrderSerializer(updated).data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def imaging_order_report_api(request, order_id):
    if not _can_report(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = ImagingOrder.objects.get(pk=order_id)
    except ImagingOrder.DoesNotExist:
        return Response({'detail': 'Imaging order not found.'}, status=status.HTTP_404_NOT_FOUND)

    report, _ = ImagingReport.objects.get_or_create(order=order)

    if request.method == 'GET':
        return Response(ImagingReportSerializer(report).data, status=status.HTTP_200_OK)

    serializer = ImagingReportSerializer(report, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    updated = serializer.save(reported_by=request.user)

    if updated.is_critical and not updated.critical_notified_at:
        updated.critical_notified_at = timezone.now()
        updated.save(update_fields=['critical_notified_at'])

    if order.status in {'ORDERED', 'SCHEDULED', 'IN_PROGRESS'}:
        order.status = 'REPORTED'
        if not order.completed_at:
            order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at'])

    return Response(ImagingReportSerializer(updated).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def imaging_order_release_api(request, order_id):
    if not _can_report(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        order = ImagingOrder.objects.get(pk=order_id)
    except ImagingOrder.DoesNotExist:
        return Response({'detail': 'Imaging order not found.'}, status=status.HTTP_404_NOT_FOUND)

    report, _ = ImagingReport.objects.get_or_create(order=order)
    report.report_status = 'FINAL'
    report.released_by = request.user
    report.released_at = timezone.now()
    report.save(update_fields=['report_status', 'released_by', 'released_at'])

    order.status = 'RELEASED'
    order.released_at = timezone.now()
    order.save(update_fields=['status', 'released_at'])

    return Response(
        {
            'detail': 'Imaging report released to patient history.',
            'order': ImagingOrderSerializer(order).data,
            'report': ImagingReportSerializer(report).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def imaging_order_attachments_api(request, order_id):
    try:
        order = ImagingOrder.objects.get(pk=order_id)
    except ImagingOrder.DoesNotExist:
        return Response({'detail': 'Imaging order not found.'}, status=status.HTTP_404_NOT_FOUND)

    if _is_patient(request.user):
        if order.patient.user_id != request.user.id:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        if request.method != 'GET':
            return Response({'detail': 'Patients cannot upload attachments.'}, status=status.HTTP_403_FORBIDDEN)
    elif not _is_staff(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = ImagingAttachmentSerializer(order.attachments.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = ImagingAttachmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(order=order, uploaded_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def imaging_worklist_api(request):
    if not _is_staff(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = ImagingOrder.objects.select_related('patient__user', 'catalog_item').filter(
        status__in=['ORDERED', 'SCHEDULED', 'IN_PROGRESS', 'REPORTED']
    )
    serializer = ImagingOrderSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def imaging_history_api(request):
    if _is_patient(request.user):
        try:
            patient = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    elif _is_staff(request.user):
        patient_id = request.GET.get('patient_id')
        if not patient_id:
            return Response({'detail': 'patient_id is required for staff history lookup.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = PatientProfile.objects.get(pk=patient_id)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = ImagingOrder.objects.select_related(
        'patient__user',
        'catalog_item',
        'assigned_radiologist__user',
    ).filter(patient=patient, status__in=['REPORTED', 'RELEASED'])

    serializer = ImagingOrderSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
