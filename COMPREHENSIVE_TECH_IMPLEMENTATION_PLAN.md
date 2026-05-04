# Comprehensive Tech Implementation Plan for MediMind
## Integration of BIT Curriculum + Hospital Project Requirements

---

## EXECUTIVE SUMMARY

This plan implements a production-grade hospital management system that demonstrates all major tech concepts from BIT Semesters 1-6. The system will have:

- **Core hospital workflow**: 5 roles (patient, doctor, receptionist, lab, admin)
- **AI/ML features**: Heart risk, no-show prediction, drug checker (visible, not core)
- **Security focus**: JWT auth, 2FA, HTTPS/TLS, RBAC, audit trails
- **Payment system**: Khalti online + cash-at-hospital option (auto-mark paid online)
- **Real-time features**: Live notifications, WebSocket support
- **Cloud-ready**: Docker, Redis, PostgreSQL, horizontal scalability
- **Enterprise features**: Comprehensive logging, backup/recovery, monitoring

**Total implementation time**: 12-16 weeks (including cleanup, development, testing)

---

## PHASE 1: CLEANUP & FOUNDATION (Weeks 1-2)

### 1.1 Project Cleanup
**Objective**: Remove 8 extra apps, simplify 3 others

**Apps to DELETE immediately**:
```
- emergency/
- radiology/
- surgery/
- inpatient/
- pharmacy/ (dispensing workflow)
- quality_compliance/
- inventory/
- rooms/ (can defer bed management)
```

**Apps to SIMPLIFY**:
```
1. lab/ → Remove QC, critical values; keep test order/result/release
2. payments/ → Remove insurance/claims; keep simple Payment(amount, status, method)
3. appointments/ → Remove advanced queue ops; keep basic waiting list
```

**Steps**:
1. Remove each app from `settings.INSTALLED_APPS`
2. Remove URL patterns from `urls.py`
3. Check for ForeignKey references and handle migrations
4. Delete app folder
5. Remove frontend pages for deleted apps
6. Run tests after each deletion

**Effort**: 8-12 hours

**Tech Demonstrated**: BIT 302 (Software Engineering - refactoring), Git version control

---

### 1.2 Database Schema Cleanup
**Objective**: Finalize ERD, normalize tables, create indexes

**ERD (Entity-Relationship Diagram)**:
```
User (base class)
  ├─ PatientProfile (1:1 with PATIENT role)
  ├─ Doctor (1:1 with DOCTOR role)
  └─ [roles: patient, doctor, receptionist, lab_technician, admin]

Doctor (1:N) ─ Specialization
Doctor (1:N) ─ DoctorSchedule
Doctor (1:N) ─ Appointment

PatientProfile (1:N) ─ Appointment
PatientProfile (1:N) ─ Review
PatientProfile (1:N) ─ Payment
PatientProfile (1:N) ─ LabTest

Appointment (1:1) ─ TriageAssessment
Appointment (1:1) ─ Prescription
Appointment (1:N) ─ LabTest
Appointment (1:N) ─ Payment

Prescription (1:N) ─ PrescriptionItem
Doctor (1:N) ─ Prescription

LabTest (1:N) ─ LabResult
LabTest (1:N) ─ LabSample
PatientProfile (1:N) ─ LabResult

Review (1:1) ─ Appointment
Review (1:N) ─ Doctor
```

**Normalization**:
- Ensure 3NF (Third Normal Form)
- No transitive dependencies
- Example: `doctor_specialization` should be separate table, not denormalized into `Doctor`

**Indexing**:
```sql
CREATE INDEX idx_user_email ON users_user(email);
CREATE INDEX idx_appointment_patient ON appointments_appointment(patient_id);
CREATE INDEX idx_appointment_doctor ON appointments_appointment(doctor_id);
CREATE INDEX idx_appointment_date ON appointments_appointment(scheduled_date);
CREATE INDEX idx_lab_test_patient ON lab_labtest(patient_id);
CREATE INDEX idx_lab_result_test ON lab_labresult(lab_test_id);
CREATE INDEX idx_payment_patient ON payments_payment(patient_id);
```

**Effort**: 4-6 hours

**Tech Demonstrated**: BIT 202 (DBMS - normalization, indexing), BIT 352 (DB Admin - optimization)

---

## PHASE 2: SECURITY & AUTHENTICATION (Weeks 3-4)

### 2.1 JWT Token Implementation
**Objective**: Implement stateless JWT authentication with refresh tokens

**Architecture**:
```
1. User login (email + password)
   ↓
2. Validate credentials (Django password hasher)
   ↓
3. Issue access token (15 min expiry) + refresh token (7 days)
   ↓
4. Client stores tokens (access in memory, refresh in secure cookie)
   ↓
5. Each API request includes access token in `Authorization: Bearer <token>` header
   ↓
6. If access token expires, use refresh token to get new access token
   ↓
7. Log out: Blacklist refresh token in Redis
```

**Implementation**:
```python
# backend/hms_project/settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# backend/users/views.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import AccessToken

class LoginView(TokenObtainPairView):
    def post(self, request):
        # Validate email + password
        # Issue tokens
        # Log login event to audit trail
        pass
```

**Effort**: 2-3 hours

**Tech Demonstrated**: BIT 303 (Security - authentication, cryptography), BIT 251 (Web - API design)

---

### 2.2 Two-Factor Authentication (2FA)
**Objective**: Add OTP-based 2FA for high-risk operations

**Flow**:
```
User login → Check if 2FA enabled → Send OTP to email/SMS
↓
User submits OTP → Verify OTP (in Redis, 10 min expiry) → Issue JWT
```

**Implementation**:
```python
# backend/users/models.py
class TwoFactorCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

# backend/users/views.py (Redis-backed)
def send_otp(user):
    otp = ''.join(random.choices('0123456789', k=6))
    redis.set(f'otp:{user.id}', otp, ex=600)  # 10 min expiry
    send_email(user.email, f'Your OTP: {otp}')

def verify_otp(user, otp):
    stored_otp = redis.get(f'otp:{user.id}')
    if stored_otp == otp:
        redis.delete(f'otp:{user.id}')
        return True
    return False
```

**Effort**: 3-4 hours

**Tech Demonstrated**: BIT 303 (Security), BIT 254 (Networks - distributed OTP storage in Redis)

---

### 2.3 Role-Based Access Control (RBAC)
**Objective**: Ensure each role can only access allowed endpoints

**Roles**:
```
PATIENT:
  - View own appointments, prescriptions, lab results, payments
  - Book appointments
  - Pay bills
  - Leave reviews after completed appointment

DOCTOR:
  - View own appointments
  - Complete appointments
  - Write prescriptions
  - Update patient medical records
  - View own reviews/ratings

RECEPTIONIST:
  - Create patient profiles
  - Book appointments on behalf of patients
  - View basic patient info for registration
  - Manage waiting queue

LAB TECHNICIAN:
  - View lab tests assigned to their facility
  - Enter test results
  - Upload samples
  - Release reports

ADMIN:
  - Manage users (create, edit, delete)
  - Assign roles
  - View system settings
  - View audit logs
  - Access approvals center
  - Export reports
```

**Implementation (DRF permissions)**:
```python
# backend/appointments/permissions.py
from rest_framework.permissions import BasePermission

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'PATIENT'

class IsDoctorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['DOCTOR', 'ADMIN']

# backend/appointments/views.py
class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPatientOrDoctorOrReceptionist]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return Appointment.objects.filter(patient=user.patientprofile)
        elif user.role == 'DOCTOR':
            return Appointment.objects.filter(doctor=user.doctor)
        elif user.role == 'RECEPTIONIST':
            return Appointment.objects.all()
```

**Effort**: 3-4 hours

**Tech Demonstrated**: BIT 303 (Access control), BIT 253 (System design)

---

### 2.4 HTTPS/TLS & Security Headers
**Objective**: Encrypt all traffic, add security headers

**Already implemented in Caddyfile**:
```
Strict-Transport-Security: Force HTTPS
X-Content-Type-Options: Prevent MIME sniffing
X-Frame-Options: Prevent clickjacking
Content-Security-Policy: Control resource loading
```

**Settings**:
```python
# backend/hms_project/settings.py (production only)
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Effort**: 1-2 hours

**Tech Demonstrated**: BIT 303 (Cryptography, TLS), BIT 254 (Network security)

---

## PHASE 3: PAYMENT SYSTEM IMPLEMENTATION (Weeks 5-6)

### 3.1 Khalti Payment Gateway Integration
**Objective**: Enable online payment via Khalti, auto-mark as paid

**Flow**:
```
Patient views bill → Clicks "Pay Online" → Khalti payment page
↓
Patient enters card/wallet details → Khalti processes → Success/Failure
↓
Khalti sends webhook to our server → Verify signature → Update payment status
↓
If successful: Mark payment as PAID, send confirmation email
If failed: Keep as PENDING, allow retry
```

**Implementation**:
```python
# backend/payments/models.py
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash at Hospital'),
        ('KHALTI', 'Khalti Online'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

# backend/payments/views.py
from rest_framework.views import APIView

class KhaltiInitializeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        payment_id = request.data.get('payment_id')
        payment = Payment.objects.get(id=payment_id)
        
        # Prepare Khalti payload
        khalti_payload = {
            'public_key': settings.KHALTI_PUBLIC_KEY,
            'transaction_uuid': str(uuid.uuid4()),
            'transaction_amount': int(payment.amount * 100),  # In paisa
            'product_name': f'Appointment Payment #{payment.appointment.id}',
            'product_identity': str(payment.id),
            'success_url': 'http://localhost:3000/payments/success',
            'failure_url': 'http://localhost:3000/payments/failure',
        }
        
        return Response(khalti_payload)

class KhaltiCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        amount = request.data.get('amount')
        
        # Verify token with Khalti
        response = requests.post(
            'https://khalti.com/api/v2/payment/verify/',
            headers={'Authorization': f'Key {settings.KHALTI_SECRET_KEY}'},
            data={'token': token, 'amount': amount}
        )
        
        if response.status_code == 200:
            data = response.json()
            payment = Payment.objects.get(id=data['product_identity'])
            payment.status = 'PAID'
            payment.transaction_id = data['transaction_id']
            payment.paid_at = timezone.now()
            payment.save()
            
            # Send confirmation email
            send_payment_confirmation_email(payment.appointment.patient.user.email)
            
            return Response({'status': 'success'})
        else:
            return Response({'status': 'failed'}, status=400)
```

**Frontend (React)**:
```typescript
// frontend/src/pages/Payments/CheckoutModal.tsx
const handleKhaltiPayment = async (paymentId: string) => {
  try {
    const res = await fetch('/api/payments/khalti/initialize/', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${accessToken}` },
      body: JSON.stringify({ payment_id: paymentId })
    });
    const data = await res.json();
    
    // Load Khalti SDK
    if (window.KhaltiCheckout) {
      const checkout = new window.KhaltiCheckout({
        publicKey: data.public_key,
        productIdentity: data.product_identity,
        productName: data.product_name,
        productUrl: window.location.href,
        eventHandler: {
          onSuccess: (payload) => {
            // Send token to backend for verification
            fetch('/api/payments/khalti/callback/', {
              method: 'POST',
              body: JSON.stringify({ 
                token: payload.token, 
                amount: payload.amount 
              })
            });
          }
        }
      });
      checkout.show();
    }
  } catch (error) {
    console.error('Khalti payment failed:', error);
  }
};
```

**Effort**: 6-8 hours

**Tech Demonstrated**: BIT 251 (Web API), BIT 353 (Payment processing), API integration

---

### 3.2 Payment Options: Online + Cash Later
**Objective**: Allow patients to pay online or mark as "pay later"

**Implementation**:
```python
# Backend validation
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'method', 'status']
    
    def validate_method(self, value):
        # Only CASH or KHALTI allowed
        if value not in ['CASH', 'KHALTI']:
            raise ValidationError('Invalid payment method')
        return value

# Frontend: Show two buttons
{
  status === 'PENDING' && (
    <div className="payment-options">
      <button onClick={() => handleKhaltiPayment(paymentId)}>
        💳 Pay Online with Khalti
      </button>
      <button onClick={() => markAsPayLater(paymentId)}>
        📋 Pay Later at Hospital
      </button>
    </div>
  )
}

# Backend: Mark as pay later
def mark_as_pay_later(payment):
    payment.method = 'CASH'
    payment.status = 'PENDING'  # Still pending until paid
    payment.save()
    # Send notification: Payment due at hospital
    notify_patient(f'Payment of Rs. {payment.amount} due at hospital')
```

**Effort**: 2-3 hours

**Tech Demonstrated**: BIT 251 (API design), UX/UI decision logic

---

## PHASE 4: REAL-TIME FEATURES (Week 7)

### 4.1 Live Notifications System
**Objective**: Real-time notifications for key events

**Events that trigger notifications**:
1. Appointment confirmed
2. Appointment reminder (1 hour before)
3. Lab result ready
4. Prescription ready
5. Payment received
6. Doctor review added

**Implementation using WebSockets + Redis**:
```python
# backend/notifications/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        self.user_group_name = f'user_{self.user_id}'
        
        # Add user to group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    # Send notification to specific user
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': event['notification_type'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

# backend/appointments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
import json

@receiver(post_save, sender=Appointment)
def send_appointment_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        
        # Notify patient
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.patient.user.id}',
            {
                'type': 'send_notification',
                'notification_type': 'APPOINTMENT_CREATED',
                'message': f'Appointment scheduled with {instance.doctor.user.first_name}',
                'timestamp': str(timezone.now())
            }
        )
        
        # Notify doctor
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.doctor.user.id}',
            {
                'type': 'send_notification',
                'notification_type': 'NEW_APPOINTMENT',
                'message': f'New appointment with {instance.patient.user.first_name}',
                'timestamp': str(timezone.now())
            }
        )
```

**Frontend (React with WebSocket)**:
```typescript
// frontend/src/hooks/useNotifications.ts
import { useEffect, useState } from 'react';

export const useNotifications = (accessToken: string) => {
  const [notifications, setNotifications] = useState([]);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/notifications/`);
    
    ws.onopen = () => {
      // Send token for authentication
      ws.send(JSON.stringify({ token: accessToken }));
    };
    
    ws.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      setNotifications(prev => [notification, ...prev]);
      
      // Show toast notification
      toast({
        title: notification.notification_type,
        description: notification.message,
        duration: 5000
      });
    };
    
    return () => ws.close();
  }, [accessToken]);
  
  return notifications;
};
```

**Effort**: 4-6 hours

**Tech Demonstrated**: BIT 254 (WebSockets, real-time communication), BIT 301 (Frontend state management)

---

## PHASE 5: AI/ML FEATURES (Week 8)

### 5.1 Heart Risk Assessment
**Objective**: Framingham risk score integration

**Implementation**:
```python
# backend/heart_risk/models.py
from sklearn.preprocessing import StandardScaler
import numpy as np

class HeartRiskAssessment(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    age = models.IntegerField()
    sex = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    total_cholesterol = models.IntegerField()  # mg/dL
    hdl_cholesterol = models.IntegerField()
    systolic_bp = models.IntegerField()
    is_smoker = models.BooleanField()
    risk_score = models.FloatField(null=True)
    risk_level = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_risk(self):
        # Framingham 10-year risk calculation
        if self.sex == 'M':
            score = (3.06 * np.log(self.age) - 
                     12.63 * np.log(self.total_cholesterol) + 
                     11.09 * np.log(self.hdl_cholesterol) - 
                     7.99 * np.log(self.systolic_bp) + 
                     3.11 * self.is_smoker)
        else:
            score = (2.32 * np.log(self.age) - 
                     7.09 * np.log(self.total_cholesterol) + 
                     1.12 * np.log(self.hdl_cholesterol) - 
                     0.39 * self.systolic_bp + 
                     2.76 * self.is_smoker)
        
        self.risk_score = score
        
        # Classify risk
        if score < 5:
            self.risk_level = 'LOW'
        elif score < 10:
            self.risk_level = 'MEDIUM'
        else:
            self.risk_level = 'HIGH'
        
        self.save()

# backend/heart_risk/views.py
class HeartRiskAssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = HeartRiskAssessmentSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        # Doctor submits patient vital signs
        assessment = HeartRiskAssessment.objects.create(
            patient=request.data['patient_id'],
            age=request.data['age'],
            sex=request.data['sex'],
            total_cholesterol=request.data['total_cholesterol'],
            hdl_cholesterol=request.data['hdl_cholesterol'],
            systolic_bp=request.data['systolic_bp'],
            is_smoker=request.data['is_smoker']
        )
        assessment.calculate_risk()
        return Response(HeartRiskAssessmentSerializer(assessment).data)
```

**Effort**: 3-4 hours

**Tech Demonstrated**: BIT 252 (AI), STA 154 (Statistics - Framingham algorithm)

---

### 5.2 No-Show Prediction
**Objective**: Predict which appointments patients will miss

**Implementation**:
```python
# backend/no_show_predictor/models.py
import pickle
from sklearn.ensemble import RandomForestClassifier

class NoShowPredictionModel:
    def __init__(self):
        # Load pre-trained model (or train if doesn't exist)
        try:
            self.model = pickle.load(open('models/no_show_model.pkl', 'rb'))
        except:
            self.train_model()
    
    def train_model(self):
        # Collect historical appointment data
        appointments = Appointment.objects.filter(
            status__in=['COMPLETED', 'NO_SHOW']
        )
        
        X = []
        y = []
        
        for appt in appointments:
            features = [
                appt.patient.age,
                appt.doctor.rating or 0,
                appt.scheduled_date.weekday(),  # Day of week
                appt.scheduled_date.hour,  # Time of day
                appt.patient.previous_no_shows,
                1 if appt.patient.user.gender == 'M' else 0,
            ]
            X.append(features)
            y.append(1 if appt.status == 'NO_SHOW' else 0)
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100)
        self.model.fit(X, y)
        
        # Save model
        pickle.dump(self.model, open('models/no_show_model.pkl', 'wb'))
    
    def predict(self, appointment):
        features = [[
            appointment.patient.age,
            appointment.doctor.rating or 0,
            appointment.scheduled_date.weekday(),
            appointment.scheduled_date.hour,
            appointment.patient.previous_no_shows,
            1 if appointment.patient.user.gender == 'M' else 0,
        ]]
        
        prob = self.model.predict_proba(features)[0][1]  # Prob of no-show
        return {
            'no_show_probability': prob,
            'risk_level': 'HIGH' if prob > 0.4 else 'MEDIUM' if prob > 0.2 else 'LOW'
        }

# Celery task to run nightly
@periodic_task(run_every=crontab(hour=22, minute=0))
def predict_tomorrow_no_shows():
    tomorrow = date.today() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        scheduled_date__date=tomorrow,
        status='SCHEDULED'
    )
    
    predictor = NoShowPredictionModel()
    
    for appt in appointments:
        prediction = predictor.predict(appt)
        
        if prediction['no_show_probability'] > 0.4:
            # Send reminder SMS/email
            send_reminder(appt.patient.user.email)
            send_reminder_sms(appt.patient.user.phone)
```

**Effort**: 4-5 hours

**Tech Demonstrated**: BIT 252 (AI/ML), BIT 302 (ML pipeline), BIT 254 (Periodic tasks)

---

### 5.3 Drug Interaction Checker
**Objective**: Alert doctor/pharmacist about potential drug interactions

**Implementation**:
```python
# backend/drug_checker/models.py
class DrugInteraction(models.Model):
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('SEVERE', 'Severe'),
    ]
    
    drug_1 = models.ForeignKey('Medication', on_delete=models.CASCADE, related_name='interactions_as_drug1')
    drug_2 = models.ForeignKey('Medication', on_delete=models.CASCADE, related_name='interactions_as_drug2')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    management = models.TextField()

class Medication(models.Model):
    name = models.CharField(max_length=100)
    dose_unit = models.CharField(max_length=50)  # mg, mcg, etc.
    category = models.CharField(max_length=50)  # Antibiotic, Antihypertensive, etc.

# backend/drug_checker/views.py
class CheckInteractionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        drug_ids = request.data.get('drug_ids', [])
        
        interactions = []
        
        # Check all pairs of drugs
        for i in range(len(drug_ids)):
            for j in range(i+1, len(drug_ids)):
                drug_1_id = drug_ids[i]
                drug_2_id = drug_ids[j]
                
                interaction = DrugInteraction.objects.filter(
                    Q(drug_1_id=drug_1_id, drug_2_id=drug_2_id) |
                    Q(drug_1_id=drug_2_id, drug_2_id=drug_1_id)
                ).first()
                
                if interaction:
                    interactions.append({
                        'drug_1': interaction.drug_1.name,
                        'drug_2': interaction.drug_2.name,
                        'severity': interaction.severity,
                        'description': interaction.description,
                        'management': interaction.management
                    })
        
        return Response({
            'has_interactions': len(interactions) > 0,
            'interactions': interactions
        })
```

**Frontend (React) - embedded in prescription form**:
```typescript
const handleCheckInteractions = async (drugs: string[]) => {
  const res = await fetch('/api/drug-checker/check/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${accessToken}` },
    body: JSON.stringify({ drug_ids: drugs })
  });
  
  const data = await res.json();
  
  if (data.has_interactions) {
    data.interactions.forEach(interaction => {
      toast({
        variant: interaction.severity === 'SEVERE' ? 'destructive' : 'warning',
        title: `⚠️ ${interaction.severity} Interaction`,
        description: `${interaction.drug_1} + ${interaction.drug_2}: ${interaction.description}`
      });
    });
  }
};
```

**Effort**: 3-4 hours

**Tech Demonstrated**: BIT 252 (AI - knowledge base), BIT 251 (API), Data modeling

---

## PHASE 6: DATABASE & MONITORING (Week 9)

### 6.1 Database Optimization & Replication
**Objective**: Production-ready database with backups and monitoring

**Optimization**:
```sql
-- Indexing strategy
CREATE INDEX idx_user_email ON users_user(email) WHERE is_active = true;
CREATE INDEX idx_appointment_patient_date ON appointments_appointment(patient_id, scheduled_date DESC);
CREATE INDEX idx_appointment_doctor_date ON appointments_appointment(doctor_id, scheduled_date DESC);
CREATE INDEX idx_lab_test_patient_status ON lab_labtest(patient_id, status);
CREATE INDEX idx_payment_status ON payments_payment(status) WHERE status = 'PENDING';

-- Query optimization (Django ORM)
# Instead of:
appointments = Appointment.objects.all()
for appt in appointments:
    print(appt.doctor.user.first_name)  # N+1 query problem

# Use:
appointments = Appointment.objects.select_related('doctor__user').all()
```

**Replication** (if scaling):
```yaml
# docker-compose.yml - PostgreSQL with replica
services:
  db-primary:
    image: postgres:16
    environment:
      POSTGRES_REPLICATION_MODE: master
  
  db-replica:
    image: postgres:16
    environment:
      POSTGRES_REPLICATION_MODE: replica
      POSTGRES_MASTER_SERVICE: db-primary
```

**Backup Strategy**:
```bash
# Daily backup script (already in backend/backup_cron)
0 2 * * * pg_dump -h db -U hms_user -d hms_db -F c -f /backups/hms_db_$(date +%Y%m%d).dump

# Monthly offsite backup
0 3 1 * * aws s3 cp /backups/hms_db_*.dump s3://hospital-backups/
```

**Effort**: 2-3 hours

**Tech Demonstrated**: BIT 352 (Database admin), BIT 351 (Distributed systems)

---

### 6.2 Monitoring & Alerting
**Objective**: Production monitoring with Netdata, alerting on issues

**Metrics to monitor**:
```
Backend:
- API response time (< 200ms for 95th percentile)
- Error rate (< 0.5%)
- CPU usage (< 70%)
- Memory usage (< 80%)

Database:
- Query execution time (< 100ms)
- Connection count (< 80 of max)
- Disk usage (< 80%)
- Replication lag (< 1s)

Payments:
- Khalti payment success rate (> 98%)
- Failed payments (alert if > 5 in 1 hour)

Lab:
- Test turnaround time (alert if > 24 hours)
```

**Alerts** (via Netdata + email):
```
if http_requests_5xx > 10 in 5min → email admin
if db_connection_count > 90 → email DBA
if disk_usage > 85% → email ops
if khalti_failure_rate > 2% → email payments team
```

**Effort**: 2-3 hours

**Tech Demonstrated**: BIT 351 (Monitoring), BIT 6 (System administration)

---

## PHASE 7: TESTING & DEPLOYMENT (Week 10-11)

### 7.1 Testing Strategy
**Objective**: Comprehensive test coverage (80%+)

**Testing pyramid**:
```
Unit Tests (40%):
- Test individual functions/methods in isolation
- Example: test heart risk calculation, OTP generation, payment validation
- Tools: pytest, Django TestCase

Integration Tests (30%):
- Test interactions between components
- Example: API endpoints, database operations, signal handlers
- Tools: Django REST Framework test client

System Tests (20%):
- Test complete workflows
- Example: User registration → appointment booking → lab test → payment
- Tools: Selenium (browser automation)

E2E Tests (10%):
- Test from user perspective
- Example: Frontend + Backend + Database
- Tools: Playwright, Cypress
```

**Example unit test**:
```python
# backend/heart_risk/tests.py
import pytest
from heart_risk.models import HeartRiskAssessment

def test_heart_risk_low():
    assessment = HeartRiskAssessment(
        age=30,
        sex='M',
        total_cholesterol=180,
        hdl_cholesterol=50,
        systolic_bp=110,
        is_smoker=False
    )
    assessment.calculate_risk()
    assert assessment.risk_level == 'LOW'

def test_heart_risk_high():
    assessment = HeartRiskAssessment(
        age=65,
        sex='M',
        total_cholesterol=280,
        hdl_cholesterol=30,
        systolic_bp=160,
        is_smoker=True
    )
    assessment.calculate_risk()
    assert assessment.risk_level == 'HIGH'
```

**Example API test**:
```python
# backend/appointments/tests.py
from rest_framework.test import APIClient
from appointments.models import Appointment

def test_book_appointment():
    client = APIClient()
    client.force_authenticate(user=patient_user)
    
    response = client.post('/api/appointments/', {
        'doctor_id': doctor.id,
        'scheduled_date': '2026-05-10T10:00:00Z'
    })
    
    assert response.status_code == 201
    assert Appointment.objects.filter(patient=patient).count() == 1
```

**Effort**: 8-12 hours

**Tech Demonstrated**: BIT 302 (Software engineering - testing), Test-driven development

---

### 7.2 Deployment Pipeline
**Objective**: Automated CI/CD from code to production

**GitHub Actions workflow** (.github/workflows/ci.yml):
```yaml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: hms_test
          POSTGRES_USER: hms_user
          POSTGRES_PASSWORD: test
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          python manage.py test --noinput
      
      - name: Run linting
        run: |
          flake8 backend/ --max-line-length=120
      
      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build
      
      - name: Deploy to staging (on PR merge to develop)
        if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
        run: |
          # Deploy to staging server
          ssh deploy@staging-server "cd /app && git pull && docker-compose up -d"
      
      - name: Deploy to production (on PR merge to main)
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          # Deploy to production server (requires manual approval)
          ssh deploy@prod-server "cd /app && git pull && docker-compose up -d"
```

**Effort**: 2-3 hours

**Tech Demonstrated**: BIT 302 (CI/CD), DevOps, Git workflows

---

## PHASE 8: DOCUMENTATION & HANDOFF (Week 12)

### 8.1 API Documentation
- Swagger/OpenAPI auto-generated from DRF
- Postman collection for manual testing
- Endpoint reference guide

### 8.2 Deployment Documentation
- Server setup guide
- Docker Compose configuration
- Environment variables reference
- Backup/restore procedures
- Monitoring setup guide

### 8.3 Developer Guide
- Architecture overview
- Database schema (ERD)
- Code structure and naming conventions
- How to add new endpoints
- How to deploy updates

**Effort**: 4-6 hours

---

## TECHNOLOGY STACK SUMMARY

| Component | Technology | BIT Course |
|-----------|-----------|-----------|
| **Backend API** | Django REST Framework | BIT 251 |
| **Database** | PostgreSQL 16 | BIT 202, 352 |
| **Cache/Queue** | Redis + Celery | BIT 254, 204 |
| **Authentication** | JWT + 2FA | BIT 303 |
| **Frontend** | React + Next.js + TypeScript | BIT 301 |
| **Payments** | Khalti API | BIT 251 |
| **Real-time** | WebSockets (Django Channels) | BIT 254 |
| **AI/ML** | Scikit-learn, Pandas | BIT 252, STA 154 |
| **Containerization** | Docker + Docker Compose | BIT 101, 351 |
| **Reverse Proxy** | Caddy (TLS) | BIT 254 |
| **Monitoring** | Netdata | BIT 351 |
| **CI/CD** | GitHub Actions | BIT 302 |
| **Testing** | Pytest, Jest, Playwright | BIT 302 |

---

## TIMELINE & EFFORT ESTIMATION

```
PHASE 1: Cleanup (Weeks 1-2)               12 hours
PHASE 2: Security & Auth (Weeks 3-4)       12 hours
PHASE 3: Payment System (Weeks 5-6)        12 hours
PHASE 4: Real-time (Week 7)                 6 hours
PHASE 5: AI/ML (Week 8)                    12 hours
PHASE 6: DB & Monitoring (Week 9)           6 hours
PHASE 7: Testing & Deployment (Week 10-11) 16 hours
PHASE 8: Documentation (Week 12)            6 hours
---
TOTAL: 82 hours (12 weeks × 7 hours/week)
```

**With parallel work and team of 2-3**: 6-8 weeks
**With single developer (you)**: 12-16 weeks

---

## SUCCESS CRITERIA

By end of Phase 8, the system should have:

✅ Clean, minimal codebase (5 core + 3 AI apps only)
✅ Secure authentication (JWT + 2FA)
✅ Production-ready database (indexed, backed up, monitored)
✅ Online payment working (Khalti + cash-later option)
✅ Real-time notifications (WebSocket)
✅ AI features visible (heart risk, no-show prediction, drug checker)
✅ Comprehensive tests (80%+ coverage)
✅ CI/CD pipeline (auto-test and auto-deploy)
✅ Full documentation (API, deployment, developer guide)
✅ Monitoring and alerting (Netdata + email)
✅ All BIT Semester 1-6 tech concepts demonstrated

