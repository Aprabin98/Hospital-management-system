"""
Drug Interaction Checker System
Models for drug database and interaction checking
Located in: prescriptions app since it's prescription-related
"""

from django.db import models
from django.db.models import Q


class Drug(models.Model):
    """Medicine/Drug database"""
    CATEGORY_CHOICES = [
        ('ANTIBIOTIC', 'Antibiotic'),
        ('ANTIHISTAMINE', 'Antihistamine'),
        ('ANTIHYPERTENSIVE', 'Antihypertensive'),
        ('ANTI_INFLAMMATORY', 'Anti-inflammatory'),
        ('PAIN_RELIEVER', 'Pain Reliever'),
        ('COLD_FLU', 'Cold & Flu'),
        ('ANTACID', 'Antacid'),
        ('ANTIDIABETIC', 'Antidiabetic'),
        ('ANTICOAGULANT', 'Anticoagulant'),
        ('STATIN', 'Statin'),
        ('OTHER', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        (1, 'Mild'),
        (2, 'Moderate'),
        (3, 'Severe'),
        (4, 'Contraindicated'),
    ]

    # Basic info
    generic_name = models.CharField(max_length=200)
    brand_names = models.TextField(help_text="Comma-separated brand names")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Medical details
    description = models.TextField()
    strength = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True, help_text="mg, ml, etc.")
    
    # Safety info
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    pregnancy_category = models.CharField(max_length=2, blank=True, help_text="FDA pregnancy category: A-X")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.generic_name} ({self.brand_names.split(',')[0].strip()})"
    
    class Meta:
        unique_together = ['generic_name', 'strength']
        ordering = ['generic_name']


class DrugInteraction(models.Model):
    """Interaction between two drugs"""
    
    INTERACTION_TYPE_CHOICES = [
        ('MAJOR', 'Major Interaction'),
        ('MODERATE', 'Moderate Interaction'),
        ('MINOR', 'Minor Interaction'),
    ]

    drug1 = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='interactions_as_drug1'
    )
    drug2 = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='interactions_as_drug2'
    )
    
    # Interaction details
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPE_CHOICES)
    severity = models.IntegerField(
        choices=Drug.SEVERITY_CHOICES,
        default=2,
        help_text="1-4, higher = more severe"
    )
    
    # Clinical details
    mechanism = models.TextField(help_text="How the drugs interact")
    clinical_effect = models.TextField(help_text="What happens when combined")
    management = models.TextField(help_text="What to do about this interaction")
    
    # References
    evidence_rating = models.CharField(
        max_length=20,
        default='MODERATE',
        help_text="Quality of evidence: EXCELLENT, GOOD, MODERATE, POOR"
    )
    
    is_bidirectional = models.BooleanField(
        default=True,
        help_text="If true, both drug1+drug2 and drug2+drug1 interactions exist"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.drug1.generic_name} ↔ {self.drug2.generic_name} ({self.get_interaction_type_display()})"
    
    class Meta:
        unique_together = [('drug1', 'drug2')]
        ordering = ['-severity']


class DrugAllergy(models.Model):
    """Patient drug allergies"""
    
    ALLERGY_SEVERITY_CHOICES = [
        ('MILD', 'Mild (rash, itching)'),
        ('MODERATE', 'Moderate (swelling, difficulty breathing)'),
        ('SEVERE', 'Severe (anaphylaxis, life-threatening)'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='drug_allergies'
    )
    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='allergies'
    )
    
    # Also track by generic name in case specific drug not in DB
    generic_name = models.CharField(max_length=200)
    
    severity = models.CharField(max_length=10, choices=ALLERGY_SEVERITY_CHOICES)
    symptoms = models.TextField(help_text="Allergy symptoms experienced")
    reaction_date = models.DateField()
    
    documented_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='documented_allergies'
    )
    
    is_confirmed = models.BooleanField(default=False)
    confirmed_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.full_name} - Allergic to {self.generic_name}"
    
    class Meta:
        unique_together = ['patient', 'generic_name']


class InteractionCheckLog(models.Model):
    """Audit trail for drug interaction checks"""
    
    prescription = models.ForeignKey(
        'Prescription',
        on_delete=models.CASCADE,
        related_name='interaction_checks'
    )
    
    # When checked
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    # Results
    interactions_found = models.IntegerField(default=0)
    major_interactions = models.IntegerField(default=0)
    moderate_interactions = models.IntegerField(default=0)
    minor_interactions = models.IntegerField(default=0)
    
    allergies_found = models.IntegerField(default=0)
    
    # Human intervention
    cleared_by_doctor = models.BooleanField(default=False)
    cleared_by = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cleared_interactions'
    )
    cleared_at = models.DateTimeField(null=True, blank=True)
    doctor_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Interaction check for Rx #{self.prescription.id} - {self.interactions_found} found"
    
    class Meta:
        ordering = ['-checked_at']


# ===============================================
# DRUG INTERACTION CHECKING UTILITY FUNCTIONS
# ===============================================

class DrugChecker:
    """Utility class for checking drug interactions, allergies, etc."""
    
    @staticmethod
    def check_interactions(drugs_list):
        """
        Check interactions between multiple drugs
        Returns: {
            'interactions': [...],
            'allergies': [...],
            'warnings': [...],
        }
        """
        interactions = []
        warnings = []
        
        # Check all pairs
        for i, drug1 in enumerate(drugs_list):
            for drug2 in drugs_list[i+1:]:
                interaction = DrugInteraction.objects.filter(
                    (Q(drug1=drug1, drug2=drug2) | Q(drug1=drug2, drug2=drug1)),
                    is_active=True
                ).first()
                
                if interaction:
                    interactions.append({
                        'drug1': drug1.generic_name,
                        'drug2': drug2.generic_name,
                        'severity': interaction.severity,
                        'type': interaction.get_interaction_type_display(),
                        'mechanism': interaction.mechanism,
                        'clinical_effect': interaction.clinical_effect,
                        'management': interaction.management,
                    })
        
        return {
            'interactions': interactions,
            'major_count': sum(1 for i in interactions if i['severity'] == 4),
            'moderate_count': sum(1 for i in interactions if i['severity'] == 2),
            'minor_count': sum(1 for i in interactions if i['severity'] == 1),
        }
    
    @staticmethod
    def check_allergies(patient, drugs_list):
        """Check if patient is allergic to any drug"""
        allergies = []
        
        for drug in drugs_list:
            patient_allergies = patient.drug_allergies.filter(
                Q(drug=drug) | Q(generic_name__iexact=drug.generic_name)
            )
            
            if patient_allergies.exists():
                for allergy in patient_allergies:
                    allergies.append({
                        'drug': drug.generic_name,
                        'severity': allergy.get_severity_display(),
                        'symptoms': allergy.symptoms,
                        'date': allergy.reaction_date,
                    })
        
        return allergies
    
    @staticmethod
    def validate_prescription(prescription):
        """Full validation for drug safety"""
        medicine_names = list(
            prescription.items.exclude(medicine_name='').values_list('medicine_name', flat=True)
        )
        drug_objects = Drug.objects.filter(generic_name__in=medicine_names)
        
        interactions = DrugChecker.check_interactions(drug_objects)
        allergies = DrugChecker.check_allergies(prescription.patient, drug_objects)
        
        # Determine if prescription is safe
        is_safe = True
        warnings = []
        
        if interactions['major_count'] > 0:
            is_safe = False
            warnings.append(f"⚠️ MAJOR DRUG INTERACTIONS FOUND ({interactions['major_count']})")
        
        if allergies:
            is_safe = False
            warnings.append(f"⚠️ PATIENT HAS KNOWN ALLERGIES TO PRESCRIBED DRUGS({len(allergies)})")
        
        return {
            'is_safe': is_safe,
            'interactions': interactions,
            'allergies': allergies,
            'warnings': warnings,
        }
