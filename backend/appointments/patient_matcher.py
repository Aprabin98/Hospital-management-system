"""
Phase 2: Fuzzy patient matching service.
Prevents duplicate patient registrations using name, DOB, and phone matching.
"""
import difflib
from django.apps import apps
from users.models import PatientProfile
from .models import PatientMatch


class PatientMatchingService:
    """Fuzzy matching service for duplicate patient prevention."""
    
    # Matching thresholds
    NAME_SIMILARITY_THRESHOLD = 0.85  # 85% name match
    PHONE_MATCH_THRESHOLD = 0.9
    
    @classmethod
    def find_potential_matches(cls, full_name, date_of_birth, phone=None, email=None):
        """
        Find potential duplicate patients.
        
        Returns:
            List of (patient, match_type, confidence_score) tuples.
        """
        matches = []
        
        # Get all existing patients
        existing_patients = PatientProfile.objects.select_related('user').all()
        
        # Name + DOB matching (most reliable)
        for patient in existing_patients:
            # Exact name and DOB match
            if (
                patient.full_name.lower() == full_name.lower()
                and patient.date_of_birth
                and patient.date_of_birth == date_of_birth
            ):
                matches.append((patient, 'EXACT_NAME_DOB', 1.0))
                continue
            
            # Similar name and close DOB
            name_ratio = difflib.SequenceMatcher(
                None,
                full_name.lower(),
                patient.full_name.lower()
            ).ratio()
            
            if name_ratio >= cls.NAME_SIMILARITY_THRESHOLD:
                # Check if DOB is within 5 days (data entry error tolerance)
                if patient.date_of_birth and abs((patient.date_of_birth - date_of_birth).days) <= 5:
                    matches.append((patient, 'SIMILAR_NAME_DOB', name_ratio))
                    continue
        
        # Phone matching (phone can change but good backup)
        if phone:
            phone_normalized = cls._normalize_phone(phone)
            for patient in existing_patients:
                if patient.phone:
                    existing_phone_normalized = cls._normalize_phone(patient.phone)
                    if phone_normalized == existing_phone_normalized:
                        matches.append((patient, 'PHONE_MATCH', 0.95))
        
        # Email matching
        if email:
            for patient in existing_patients:
                patient_email = (patient.user.email or '').lower()
                if patient_email and patient_email == email.lower():
                    matches.append((patient, 'EMAIL_MATCH', 1.0))
        
        # Remove duplicates and sort by confidence
        seen = set()
        unique_matches = []
        for patient, match_type, score in sorted(matches, key=lambda x: -x[2]):
            if patient.id not in seen:
                unique_matches.append((patient, match_type, score))
                seen.add(patient.id)
        
        return unique_matches
    
    @classmethod
    def record_match(cls, new_patient, existing_patient, match_type, confidence_score):
        """Record a patient match for future review."""
        match, created = PatientMatch.objects.update_or_create(
            new_patient=new_patient,
            existing_patient=existing_patient,
            defaults={
                'match_type': match_type,
                'confidence_score': confidence_score,
            }
        )
        return match
    
    @classmethod
    def _normalize_phone(cls, phone_number):
        """Normalize phone number for comparison."""
        # Remove all non-digit characters
        return ''.join(filter(str.isdigit, str(phone_number)))
    
    @classmethod
    def merge_patients(cls, old_patient_id, new_patient_id):
        """
        Merge two patient records (old into new).
        Updates all references to point to new patient.
        """
        from appointments.models import Appointment
        
        old = PatientProfile.objects.get(id=old_patient_id)
        new = PatientProfile.objects.get(id=new_patient_id)
        
        # Merge appointments
        Appointment.objects.filter(patient=old).update(patient=new)
        
        # Merge encounters only when that model exists in this project.
        try:
            Encounter = apps.get_model('clinical', 'Encounter')
            Encounter.objects.filter(patient=old).update(patient=new)
        except LookupError:
            pass
        
        # Mark old as merged/archived
        old_user = old.user
        old_user.is_active = False
        old_user.save(update_fields=['is_active'])
        
        return new
