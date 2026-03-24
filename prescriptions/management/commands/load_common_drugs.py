"""
Management command: Load common drugs and interactions for drug interaction checker
Run: python manage.py load_common_drugs_and_interactions
"""

from django.core.management.base import BaseCommand
from prescriptions.drug_models import Drug, DrugInteraction


COMMON_DRUGS = [
    # Antibiotics
    ('Amoxicillin', 'Amoxil, Trimox', 'ANTIBIOTIC', '500mg', 'mg', 'Common penicillin antibiotic'),
    ('Azithromycin', 'Zithromax, Z-Pack', 'ANTIBIOTIC', '250mg', 'mg', 'Macrolide antibiotic'),
    ('Ciprofloxacin', 'Cipro', 'ANTIBIOTIC', '500mg', 'mg', 'Fluoroquinolone antibiotic'),
    
    # Antihistamines
    ('Cetirizine', 'Zyrtec', 'ANTIHISTAMINE', '10mg', 'mg', 'Non-drowsy antihistamine'),
    ('Loratadine', 'Claritin', 'ANTIHISTAMINE', '10mg', 'mg', 'Long-acting antihistamine'),
    
    # Antihypertensives
    ('Lisinopril', 'Prinivil', 'ANTIHYPERTENSIVE', '10mg', 'mg', 'ACE inhibitor'),
    ('Metoprolol', 'Lopressor', 'ANTIHYPERTENSIVE', '50mg', 'mg', 'Beta blocker'),
    ('Atorvastatin', 'Lipitor', 'STATIN', '20mg', 'mg', 'Cholesterol-lowering statin'),
    
    # Pain relievers
    ('Ibuprofen', 'Advil, Motrin', 'PAIN_RELIEVER', '200mg', 'mg', 'NSAID'),
    ('Acetaminophen', 'Tylenol', 'PAIN_RELIEVER', '500mg', 'mg', 'Acetaminophen'),
    ('Naproxen', 'Aleve', 'ANTI_INFLAMMATORY', '250mg', 'mg', 'NSAID'),
    
    # Anticoagulants
    ('Warfarin', 'Coumadin', 'ANTICOAGULANT', '5mg', 'mg', 'Vitamin K antagonist'),
    ('Aspirin', 'Bayer', 'ANTICOAGULANT', '81mg', 'mg', 'Low-dose aspirin'),
    
    # Antidiabetics
    ('Metformin', 'Glucophage', 'ANTIDIABETIC', '500mg', 'mg', 'First-line diabetes medication'),
    ('Glipizide', 'Glucotrol', 'ANTIDIABETIC', '5mg', 'mg', 'Sulfonylurea'),
]

# Known interactions - (generic1, generic2, type, severity, mechanism, effect, management)
INTERACTIONS = [
    # Warfarin interactions (major)
    ('Warfarin', 'Aspirin', 'MAJOR', 4, 'Additive anticoagulation', 'Increased bleeding risk', 'Avoid combination or monitor INR closely'),
    ('Warfarin', 'Ibuprofen', 'MAJOR', 4, 'NSAID inhibits warfarin metabolism', 'Increased INR, bleeding risk', 'Avoid NSAIDs, use acetaminophen instead'),
    ('Warfarin', 'Naproxen', 'MAJOR', 4, 'NSAID effects', 'Increased bleeding risk', 'Contraindicated'),
    
    # Antibiotic interactions
    ('Azithromycin', 'Warfarin', 'MODERATE', 2, 'Azithromycin increases warfarin effect', 'Elevated INR', 'Monitor INR, may need warfarin dose adjustment'),
    ('Ciprofloxacin', 'Metformin', 'MODERATE', 2, 'Altered renal function', 'Increased metformin levels', 'Monitor renal function'),
    
    # Statin interactions
    ('Atorvastatin', 'Ciprofloxacin', 'MINOR', 1, 'Minor CYP3A4 interaction', 'Slightly increased statin levels', 'Monitor for muscle pain'),
    
    # Acetaminophen safety
    ('Acetaminophen', 'Ibuprofen', 'MINOR', 1, 'Separate mechanisms', 'Can be used together for pain', 'Use at different times if preferred'),
]


class Command(BaseCommand):
    help = 'Load common drugs and interactions into database'

    def handle(self, *args, **options):
        self.stdout.write('Loading common drugs...')
        
        # Load drugs
        created_count = 0
        for generic_name, brand_names, category, strength, unit, description in COMMON_DRUGS:
            drug, created = Drug.objects.get_or_create(
                generic_name=generic_name,
                strength=strength,
                defaults={
                    'brand_names': brand_names,
                    'category': category,
                    'unit': unit,
                    'description': description,
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {created_count} drugs'))
        
        # Load interactions
        interaction_count = 0
        for generic1, generic2, int_type, severity, mechanism, effect, management in INTERACTIONS:
            try:
                drug1 = Drug.objects.get(generic_name=generic1)
                drug2 = Drug.objects.get(generic_name=generic2)
                
                interaction, created = DrugInteraction.objects.get_or_create(
                    drug1=drug1,
                    drug2=drug2,
                    defaults={
                        'interaction_type': int_type,
                        'severity': severity,
                        'mechanism': mechanism,
                        'clinical_effect': effect,
                        'management': management,
                    }
                )
                if created:
                    interaction_count += 1
            except Drug.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Drug not found: {generic1} or {generic2}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {interaction_count} interactions'))
        self.stdout.write(self.style.SUCCESS('✅ Drug database ready!'))
