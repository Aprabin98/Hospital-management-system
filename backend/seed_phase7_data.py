#!/usr/bin/env python
"""
Phase 7 Test Data Seeder - Finance & Insurance Maturity
Path: backend/seed_phase7_data.py
Creates test data for invoice, claims, pre-authorizations, and denial workflows
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
from random import randint, choice

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import PatientProfile, DoctorProfile
from appointments.models import Appointment, AppointmentSlot
from payments.models import (
    InsuranceVerification, Invoice, InvoiceLineItem, InsuranceClaim,
    ClaimAuditLog, DenialRework, InsurancePreAuth
)
from lab.models import TestBooking

User = get_user_model()

def create_test_invoices():
    """Create sample invoices in various states"""
    print("Creating test invoices...")
    
    # Get patients and insurance verifications
    patients = PatientProfile.objects.all()[:3]
    insurances = InsuranceVerification.objects.filter(status='ACTIVE')[:2]
    
    if not patients or not insurances:
        print("  ⚠️  Insufficient patients or insurance verifications. Skipping invoices.")
        return 0
    
    invoice_count = 0
    statuses = ['DRAFT', 'ISSUED', 'PAID', 'PARTIALLY_PAID']
    
    for i in range(4):
        patient = choice(patients)
        insurance = choice(insurances)
        
        subtotal = Decimal(str(randint(5000, 50000)))
        tax_amount = subtotal * Decimal('0.05')  # 5% tax
        discount_amount = Decimal(str(randint(0, 2000)))
        total_amount = subtotal + tax_amount - discount_amount
        
        status = choice(statuses)
        amount_paid = total_amount if status == 'PAID' else (total_amount * Decimal('0.5') if status == 'PARTIALLY_PAID' else Decimal('0'))
        
        invoice = Invoice.objects.create(
            invoice_number=f"INV-2024-{1001+i}",
            invoice_type='PROFORMA' if status == 'DRAFT' else 'FINAL',
            patient=patient,
            appointment=None,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            amount_paid=amount_paid,
            status=status,
            due_date=timezone.now().date() + timedelta(days=30),
            insurance_verification=insurance,
            insurance_amount=total_amount * Decimal('0.8'),
            patient_amount=total_amount * Decimal('0.2'),
            created_by=User.objects.filter(role='BILLING_OFFICER').first() or User.objects.filter(role='ADMIN').first()
        )
        
        # Create line items
        for j in range(2):
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=choice(['Consultation Fee', 'Lab Tests', 'Medication', 'Procedures', 'Room Charges']),
                quantity=randint(1, 5),
                unit_price=Decimal(str(randint(1000, 10000))),
                appointment=None,
                lab_booking=None
            )
        
        invoice_count += 1
        print(f"  ✓ Invoice {invoice.invoice_number} ({status})")
    
    return invoice_count


def create_test_claims():
    """Create sample insurance claims in various statuses"""
    print("\nCreating test insurance claims...")
    
    invoices = Invoice.objects.all()[:4]
    if not invoices:
        print("  ⚠️  No invoices found. Skipping claims.")
        return 0
    
    claim_count = 0
    statuses = ['DRAFT', 'SUBMITTED', 'PROCESSING', 'APPROVED', 'REJECTED']
    
    for i, invoice in enumerate(invoices):
        status = statuses[i % len(statuses)]
        
        claim = InsuranceClaim.objects.create(
            claim_number=f"CLM-2024-{5001+i}",
            invoice=invoice,
            patient=invoice.patient,
            insurance_verification=invoice.insurance_verification,
            claimed_amount=invoice.total_amount,
            approved_amount=invoice.total_amount if status in ['APPROVED', 'PROCESSING'] else None,
            reduction_reason="Deductible applied" if status == 'APPROVED' else None,
            status=status,
            submitted_at=timezone.now() - timedelta(days=randint(1, 45)) if status != 'DRAFT' else None,
            submitted_by=User.objects.filter(role='BILLING_OFFICER').first() or User.objects.filter(role='ADMIN').first(),
            submission_reference=f"REF-{1001+i}" if status != 'DRAFT' else None,
            submission_notes=f"Claim for invoice {invoice.invoice_number}" if status != 'DRAFT' else None
        )
        
        # Add audit log if not draft
        if status != 'DRAFT':
            ClaimAuditLog.objects.create(
                claim=claim,
                old_status='DRAFT',
                new_status=status,
                changed_by=User.objects.filter(role='ADMIN').first(),
                change_reason='Automatic status update',
                notes=f"Claim transitioned to {status}"
            )
        
        claim_count += 1
        print(f"  ✓ Claim {claim.claim_number} ({status})")
    
    return claim_count


def create_test_denials():
    """Create sample denial reworks"""
    print("\nCreating test denial reworks...")
    
    # Get rejected claims
    rejected_claims = InsuranceClaim.objects.filter(status='REJECTED')[:2]
    
    if not rejected_claims:
        # Create a rejected claim first
        invoice = Invoice.objects.first()
        if invoice:
            rejected_claim = InsuranceClaim.objects.create(
                claim_number=f"CLM-2024-{9001}",
                invoice=invoice,
                patient=invoice.patient,
                insurance_verification=invoice.insurance_verification,
                claimed_amount=invoice.total_amount,
                status='REJECTED',
                submitted_at=timezone.now() - timedelta(days=15),
                submitted_by=User.objects.filter(role='BILLING_OFFICER').first(),
                submission_reference="REF-9001",
                submission_notes="Claim for denial rework testing"
            )
            rejected_claims = [rejected_claim]
        else:
            print("  ⚠️  No invoices found. Skipping denials.")
            return 0
    
    rework_count = 0
    denial_reasons = [
        'Missing documentation',
        'Treatment code mismatch',
        'Coverage exclusion applied',
        'Pre-authorization not found',
        'Duplicate claim submission'
    ]
    
    for claim in rejected_claims:
        statuses = ['PENDING_REVIEW', 'UNDER_CORRECTION']
        
        rework = DenialRework.objects.create(
            claim=claim,
            original_denial_reason=choice(denial_reasons),
            status=choice(statuses),
            assigned_to=User.objects.filter(role='BILLING_OFFICER').first() if randint(0, 1) else None,
            correction_notes="Correcting documentation and resubmitting",
            resubmit_date=timezone.now().date() + timedelta(days=5) if randint(0, 1) else None
        )
        
        rework_count += 1
        print(f"  ✓ Denial rework for claim {claim.claim_number} ({rework.status})")
    
    return rework_count


def create_test_pre_auths():
    """Create sample pre-authorization requests"""
    print("\nCreating test pre-authorizations...")
    
    patients = PatientProfile.objects.all()[:3]
    insurances = InsuranceVerification.objects.filter(status='ACTIVE')[:2]
    
    if not patients or not insurances:
        print("  ⚠️  Insufficient patients or insurance verifications. Skipping pre-auths.")
        return 0
    
    preauth_count = 0
    treatment_codes = ['CARDIAC_BYPASS', 'KNEE_REPLACEMENT', 'CATARACT_SURGERY', 'GASTRIC_BYPASS', 'SPINE_FUSION']
    statuses = ['REQUESTED', 'APPROVED', 'REJECTED', 'PARTIAL']
    
    for i in range(4):
        patient = choice(patients)
        insurance = choice(insurances)
        status = choice(statuses)
        
        estimated_amount = Decimal(str(randint(50000, 500000)))
        approved_amount = estimated_amount if status in ['APPROVED', 'PARTIAL'] else None
        
        preauth = InsurancePreAuth.objects.create(
            patient=patient,
            insurance_verification=insurance,
            treatment_code=choice(treatment_codes),
            estimated_amount=estimated_amount,
            approved_amount=approved_amount,
            status=status,
            pre_auth_number=f"PRE-2024-{3001+i}" if status != 'REQUESTED' else None,
            valid_from=timezone.now().date() if status != 'REQUESTED' else None,
            valid_until=timezone.now().date() + timedelta(days=90) if status != 'REQUESTED' else None
        )
        
        preauth_count += 1
        print(f"  ✓ Pre-auth {preauth.pre_auth_number or 'PENDING'} ({status})")
    
    return preauth_count


def main():
    """Run all Phase 7 seed data creation"""
    print("=" * 60)
    print("PHASE 7 TEST DATA SEEDER - Finance & Insurance Maturity")
    print("=" * 60)
    
    try:
        invoice_count = create_test_invoices()
        claim_count = create_test_claims()
        denial_count = create_test_denials()
        preauth_count = create_test_pre_auths()
        
        print("\n" + "=" * 60)
        print("SEEDING SUMMARY")
        print("=" * 60)
        print(f"✅ Invoices created: {invoice_count}")
        print(f"✅ Claims created: {claim_count}")
        print(f"✅ Denial reworks created: {denial_count}")
        print(f"✅ Pre-authorizations created: {preauth_count}")
        print(f"\n🎉 Phase 7 test data seeding completed successfully!")
        print("\nYou can now test the finance APIs at:")
        print("  - GET  /api/invoices/")
        print("  - GET  /api/claims/")
        print("  - GET  /api/denial-reworks/")
        print("  - GET  /api/pre-auths/")
        print("  - GET  /api/finance/dashboard/")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
