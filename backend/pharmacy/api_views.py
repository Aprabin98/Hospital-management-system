from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from .models import MedicationInventory, DispensingTransaction, ControlledDrugLog, PharmacyAlert
from .api_serializers import (
    MedicationInventorySerializer, DispensingTransactionSerializer,
    ControlledDrugLogSerializer, PharmacyAlertSerializer
)
from prescriptions.models import Prescription
from audit.utils import log_audit_event


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def medication_inventory_api(request):
    """
    GET: List all medications in inventory with filters (expired, near_expiry, controlled, low_stock)
    POST: Add new medication batch to inventory
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = MedicationInventory.objects.all()
        
        # Filters
        expired = request.query_params.get('expired')
        near_expiry = request.query_params.get('near_expiry')
        controlled = request.query_params.get('controlled')
        blocked = request.query_params.get('blocked')
        
        if expired == 'true':
            queryset = queryset.filter(is_expired=True)
        elif expired == 'false':
            queryset = queryset.filter(is_expired=False)
        
        if near_expiry == 'true':
            queryset = queryset.filter(is_near_expiry=True, is_expired=False)
        
        if controlled == 'true':
            queryset = queryset.filter(is_controlled_drug=True)
        
        if blocked == 'true':
            queryset = queryset.filter(is_blocked=True)
        
        serializer = MedicationInventorySerializer(queryset, many=True)
        
        # Log access to controlled drugs
        if controlled == 'true':
            log_audit_event(
                user=request.user,
                action='PHARMACY_CONTROLLED_DRUGS_VIEWED',
                resource='pharmacy.MedicationInventory',
                details={'filter': 'controlled_drugs'}
            )
        
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })
    
    elif request.method == 'POST':
        data = request.data
        
        try:
            inventory = MedicationInventory.objects.create(
                medication_name=data.get('medication_name'),
                batch_number=data.get('batch_number'),
                lot_number=data.get('lot_number'),
                manufacturer=data.get('manufacturer'),
                quantity=int(data.get('quantity', 0)),
                unit=data.get('unit'),
                unit_cost=float(data.get('unit_cost', 0)),
                manufacture_date=data.get('manufacture_date'),
                expiry_date=data.get('expiry_date'),
                is_controlled_drug=data.get('is_controlled_drug', False) == 'true' or data.get('is_controlled_drug') == True,
                received_by=request.user
            )
            
            log_audit_event(
                user=request.user,
                action='PHARMACY_INVENTORY_CREATED',
                resource='pharmacy.MedicationInventory',
                resource_id=inventory.id,
                details={
                    'medication_name': inventory.medication_name,
                    'batch_number': inventory.batch_number,
                    'quantity': inventory.quantity
                }
            )
            
            serializer = MedicationInventorySerializer(inventory)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH"])
def medication_detail_api(request, medication_id):
    """
    GET: Get medication inventory details
    PATCH: Update medication inventory (quantity, status flags)
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        medication = MedicationInventory.objects.get(id=medication_id)
    except MedicationInventory.DoesNotExist:
        return Response({'detail': 'Medication not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = MedicationInventorySerializer(medication)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        data = request.data
        
        # Update quantity
        if 'quantity' in data:
            old_quantity = medication.quantity
            medication.quantity = int(data['quantity'])
            
            log_audit_event(
                user=request.user,
                action='PHARMACY_INVENTORY_UPDATED',
                resource='pharmacy.MedicationInventory',
                resource_id=medication.id,
                details={
                    'field': 'quantity',
                    'old_value': old_quantity,
                    'new_value': medication.quantity
                }
            )
        
        # Block/unblock medication
        if 'is_blocked' in data:
            medication.is_blocked = data['is_blocked'] in ['true', True]
        
        medication.save()
        serializer = MedicationInventorySerializer(medication)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def pending_dispense_queue_api(request):
    """
    GET: List prescriptions pending dispensing for pharmacy queue
    Filters: status (PENDING, APPROVED), patient_name, urgent
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get pending prescriptions (not yet dispensed)
    queryset = Prescription.objects.filter(status='ACTIVE').exclude(
        dispensing_transactions__status__in=['DISPENSED', 'REFUSED']
    ).distinct()
    
    # Filter by patient name
    patient_name = request.query_params.get('patient_name')
    if patient_name:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(patient__first_name__icontains=patient_name) |
            Q(patient__last_name__icontains=patient_name) |
            Q(patient__email__icontains=patient_name)
        )
    
    # Get pending dispensing transactions
    pending_transactions = []
    for prescription in queryset:
        # Check if already has pending dispense
        existing = DispensingTransaction.objects.filter(
            prescription=prescription,
            status__in=['PENDING', 'APPROVED']
        ).first()
        
        if not existing:
            # Create pending transaction
            transaction = DispensingTransaction.objects.create(
                prescription=prescription,
                patient=prescription.patient,
                inventory=None,  # To be selected by pharmacist
                quantity_dispensed=0,
                dispensed_by=request.user,
                status='PENDING'
            )
        else:
            transaction = existing
        
        pending_transactions.append(transaction)
    
    serializer = DispensingTransactionSerializer(pending_transactions, many=True)
    
    log_audit_event(
        user=request.user,
        action='PHARMACY_PENDING_QUEUE_VIEWED',
        resource='pharmacy.DispensingTransaction',
        details={'count': len(pending_transactions)}
    )
    
    return Response({
        'count': len(serializer.data),
        'results': serializer.data
    })


@api_view(['POST', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST", "PATCH"])
def dispense_transaction_api(request, transaction_id=None):
    """
    POST: Create new dispensing transaction for a prescription
    PATCH: Update dispensing transaction (dispense, refuse, return)
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'POST':
        data = request.data
        
        try:
            prescription = Prescription.objects.get(id=data.get('prescription_id'))
            inventory = MedicationInventory.objects.get(id=data.get('inventory_id'))
            
            # Check if expired
            if inventory.is_expired:
                return Response(
                    {'detail': 'Cannot dispense expired medication'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if blocked
            if inventory.is_blocked:
                return Response(
                    {'detail': 'Medication is blocked from dispensing'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check quantity
            quantity = int(data.get('quantity_dispensed', 0))
            if quantity > inventory.quantity:
                return Response(
                    {'detail': f'Insufficient stock. Available: {inventory.quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create transaction
            transaction = DispensingTransaction.objects.create(
                prescription=prescription,
                patient=prescription.patient,
                inventory=inventory,
                quantity_dispensed=quantity,
                is_substituted=data.get('is_substituted', False),
                substitution_reason=data.get('substitution_reason'),
                status='PENDING',
                dispensed_by=request.user,
                contraindication_checked=data.get('contraindication_checked', False),
                contraindication_notes=data.get('contraindication_notes')
            )
            
            log_audit_event(
                user=request.user,
                action='PHARMACY_DISPENSE_CREATED',
                resource='pharmacy.DispensingTransaction',
                resource_id=transaction.id,
                details={
                    'prescription_id': prescription.id,
                    'medication': inventory.medication_name,
                    'quantity': quantity
                }
            )
            
            serializer = DispensingTransactionSerializer(transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PATCH':
        data = request.data
        
        try:
            transaction = DispensingTransaction.objects.get(id=transaction_id)
        except DispensingTransaction.DoesNotExist:
            return Response({'detail': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update status
        new_status = data.get('status')
        if new_status == 'APPROVED':
            transaction.status = 'APPROVED'
            transaction.approved_by = request.user
            transaction.approved_at = timezone.now()
        
        elif new_status == 'DISPENSED':
            transaction.status = 'DISPENSED'
            transaction.dispensed_at = timezone.now()
            
            # Deduct from inventory
            transaction.inventory.quantity -= transaction.quantity_dispensed
            transaction.inventory.save()
        
        elif new_status == 'REFUSED':
            transaction.status = 'REFUSED'
            transaction.refusal_reason = data.get('reason', '')
        
        elif new_status == 'RETURNED':
            transaction.status = 'RETURNED'
            transaction.return_reason = data.get('reason', '')
            
            # Restore to inventory
            transaction.inventory.quantity += transaction.quantity_dispensed
            transaction.inventory.save()
        
        transaction.save()
        
        log_audit_event(
            user=request.user,
            action=f'PHARMACY_DISPENSE_{new_status}',
            resource='pharmacy.DispensingTransaction',
            resource_id=transaction.id,
            details={'new_status': new_status}
        )
        
        serializer = DispensingTransactionSerializer(transaction)
        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def controlled_drug_log_api(request):
    """
    GET: List controlled drug logs with filters (drug type, recorded_by, date_range)
    POST: Create controlled drug log entry
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = ControlledDrugLog.objects.all()
        
        # Filter by schedule
        schedule = request.query_params.get('schedule')
        if schedule:
            queryset = queryset.filter(dea_schedule=schedule)
        
        # Filter by date range
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        serializer = ControlledDrugLogSerializer(queryset, many=True)
        
        log_audit_event(
            user=request.user,
            action='PHARMACY_CONTROLLED_DRUGS_LOG_VIEWED',
            resource='pharmacy.ControlledDrugLog',
            details={'count': len(queryset)}
        )
        
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })
    
    elif request.method == 'POST':
        data = request.data
        
        try:
            log_entry = ControlledDrugLog.objects.create(
                medication_name=data.get('medication_name'),
                batch_number=data.get('batch_number'),
                dea_schedule=data.get('dea_schedule'),
                log_type=data.get('log_type'),
                quantity=int(data.get('quantity', 0)),
                unit=data.get('unit'),
                recorded_by=request.user,
                patient_id=data.get('patient_id'),
                transaction_date=data.get('transaction_date'),
                notes=data.get('notes'),
                witnessed_by_id=data.get('witnessed_by_id')
            )
            
            log_audit_event(
                user=request.user,
                action='PHARMACY_CONTROLLED_DRUG_LOG_CREATED',
                resource='pharmacy.ControlledDrugLog',
                resource_id=log_entry.id,
                details={
                    'medication': log_entry.medication_name,
                    'schedule': log_entry.dea_schedule,
                    'log_type': log_entry.log_type,
                    'quantity': log_entry.quantity
                }
            )
            
            serializer = ControlledDrugLogSerializer(log_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH"])
def pharmacy_alerts_api(request):
    """
    GET: List pharmacy alerts (low stock, expiry, recalls, etc)
    PATCH: Mark alert as resolved
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        queryset = PharmacyAlert.objects.all()
        
        # Filter unresolved only
        unresolved_only = request.query_params.get('unresolved', 'true')
        if unresolved_only == 'true':
            queryset = queryset.filter(is_resolved=False)
        
        # Filter by alert type
        alert_type = request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        serializer = PharmacyAlertSerializer(queryset, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })
    
    elif request.method == 'PATCH':
        data = request.data
        
        try:
            alert_id = data.get('alert_id')
            alert = PharmacyAlert.objects.get(id=alert_id)
            
            alert.is_resolved = data.get('is_resolved', True)
            alert.resolved_by = request.user
            alert.resolved_at = timezone.now()
            alert.save()
            
            log_audit_event(
                user=request.user,
                action='PHARMACY_ALERT_RESOLVED',
                resource='pharmacy.PharmacyAlert',
                resource_id=alert.id,
                details={'alert_type': alert.alert_type}
            )
            
            serializer = PharmacyAlertSerializer(alert)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def pharmacy_dashboard_api(request):
    """
    GET: Pharmacy dashboard metrics and KPIs
    Returns: counts for pending dispenses, alerts, controlled drugs, inventory status
    """
    if request.user.role not in ['ADMIN', 'PHARMACIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    
    # Count pending dispenses
    pending_dispenses = DispensingTransaction.objects.filter(status='PENDING').count()
    approved_dispenses = DispensingTransaction.objects.filter(status='APPROVED').count()
    dispensed_today = DispensingTransaction.objects.filter(
        status='DISPENSED',
        dispensed_at__date=today
    ).count()
    
    # Count alerts
    unresolved_alerts = PharmacyAlert.objects.filter(is_resolved=False).count()
    expired_meds = MedicationInventory.objects.filter(is_expired=True).count()
    near_expiry_meds = MedicationInventory.objects.filter(is_near_expiry=True, is_expired=False).count()
    
    # Count controlled drugs
    controlled_meds = MedicationInventory.objects.filter(is_controlled_drug=True).count()
    controlled_dispenses_today = ControlledDrugLog.objects.filter(
        transaction_date=today,
        log_type='DISPENSED'
    ).count()
    
    # Low stock items (assuming min 5 units for non-controlled)
    low_stock = MedicationInventory.objects.filter(quantity__lt=5, is_blocked=False, is_expired=False).count()
    
    log_audit_event(
        user=request.user,
        action='PHARMACY_DASHBOARD_VIEWED',
        resource='pharmacy',
        details={}
    )
    
    return Response({
        'dispenses': {
            'pending': pending_dispenses,
            'approved': approved_dispenses,
            'dispensed_today': dispensed_today,
        },
        'alerts': {
            'unresolved_alerts': unresolved_alerts,
            'expired_medications': expired_meds,
            'near_expiry_medications': near_expiry_meds,
            'low_stock_items': low_stock,
        },
        'controlled_drugs': {
            'total_controlled_items': controlled_meds,
            'dispensed_today': controlled_dispenses_today,
        },
        'inventory': {
            'total_items': MedicationInventory.objects.count(),
            'total_value': sum(float(m.quantity * m.unit_cost) for m in MedicationInventory.objects.all()),
        }
    })
