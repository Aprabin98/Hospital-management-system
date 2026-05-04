# BIT Curriculum (Semesters 1-6) → Hospital Project Tech Implementation Map

## Overview
This document maps technical concepts from the Nepal BIT (Bachelor in Information Technology) curriculum (Semesters 1-6) to concrete implementations in the MediMind Hospital Management System.

---

## SEMESTER 1: Foundations

### 1. BIT 101 - Introduction To Information Technology
**Tech Concepts**:
- System architecture (hardware/software)
- Operating systems basics
- Networking fundamentals
- Data representation

**Application in Hospital Project**:
- ✅ **Docker containerization**: Package backend, frontend, DB, Redis, Celery into containers
- ✅ **Microservices thinking**: Separate concerns (auth, appointments, lab, payments)
- ✅ **System design**: Load balancer (Caddy) + multiple backend instances

---

### 2. BIT 102 - C Programming
**Tech Concepts**:
- Low-level programming
- Memory management
- Pointers and data structures
- Performance optimization

**Application in Hospital Project**:
- ✅ **Performance tuning**: Database query optimization (indexes, caching)
- ✅ **Memory management**: Redis for caching to reduce DB queries
- ✅ **Algorithm optimization**: Efficient search for patient/doctor lookups
- ✅ **Background processing**: Celery tasks for async operations

---

### 3. BIT 103 - Digital Logic
**Tech Concepts**:
- Boolean logic
- Logic gates
- Binary operations
- Circuit design principles

**Application in Hospital Project**:
- ✅ **Role-based access control (RBAC)**: Boolean logic for permissions
  - If (user_role == 'DOCTOR' AND appointment.status == 'completed') → can_write_prescription = True
- ✅ **Business rule engine**: Complex conditions for appointment booking, lab result validation
- ✅ **State machines**: Appointment workflow (scheduled → in-progress → completed)

---

### 4. MTH 104 - Basic Mathematics
**Tech Concepts**:
- Set theory
- Probability
- Statistics basics

**Application in Hospital Project**:
- ✅ **No-show prediction**: Probability modeling (ML)
- ✅ **Heart risk assessment**: Framingham risk score (statistical calculation)
- ✅ **Appointment scheduling optimization**: Graph theory for time slot allocation

---

## SEMESTER 2: Object-Oriented & System Design

### 1. BIT 151 - Microprocessor And Computer Architecture
**Tech Concepts**:
- CPU design
- Memory hierarchy
- I/O systems
- Performance metrics

**Application in Hospital Project**:
- ✅ **Database optimization**: Understand how DB queries execute at CPU level
- ✅ **Caching strategy**: Multi-level caching (Redis → DB → disk)
- ✅ **I/O optimization**: Batch operations for bulk imports (patient registration, test results)
- ✅ **Performance monitoring**: Netdata to monitor CPU/memory usage

---

### 2. BIT 152 - Discrete Structure
**Tech Concepts**:
- Sets, relations, functions
- Combinatorics
- Graph theory
- Trees and forests

**Application in Hospital Project**:
- ✅ **Appointment scheduling graph**: Doctor → Time slots → Patients
- ✅ **Patient relationship mapping**: Parent-child relationships (if family planning)
- ✅ **Department hierarchy**: Tree structure (Hospital → Department → Doctor → Specialization)
- ✅ **Waiting list queue**: FIFO data structure for appointment queue
- ✅ **Lab result flow**: DAG (directed acyclic graph) for test order → sample → result → release

---

### 3. BIT 153 - Object Oriented Programming
**Tech Concepts**:
- Classes, objects, inheritance
- Polymorphism
- Encapsulation
- Design patterns

**Application in Hospital Project**:
- ✅ **Django ORM**: Models as classes (User, Doctor, Patient, Appointment, etc.)
- ✅ **Polymorphism**: User model with different roles (PATIENT, DOCTOR, ADMIN)
- ✅ **Inheritance**: PatientProfile extends User, Doctor extends User
- ✅ **Design patterns**:
  - **Factory pattern**: Create different user types based on role
  - **Strategy pattern**: Different payment strategies (Khalti online, cash at hospital)
  - **Observer pattern**: Notifications triggered by appointment completion
  - **Singleton pattern**: Database connection, Redis client
- ✅ **Serializers**: DRF serializers as data transformation layer

---

### 4. STA 154 - Basic Statistics
**Tech Concepts**:
- Descriptive statistics (mean, median, std dev)
- Probability distributions
- Hypothesis testing
- Correlation and regression

**Application in Hospital Project**:
- ✅ **Heart risk scoring**: Framingham calculation (uses regression)
- ✅ **No-show prediction**: Logistic regression model
- ✅ **Doctor performance metrics**: Average appointment duration, completion rate
- ✅ **Lab result validation**: Flag abnormal values using standard deviations
- ✅ **Dashboard KPIs**: Calculate average wait time, patient satisfaction trends

---

## SEMESTER 3: Data & Algorithms

### 1. BIT 201 - Data Structure And Algorithms
**Tech Concepts**:
- Arrays, linked lists, stacks, queues
- Trees, graphs, heaps
- Sorting and searching algorithms
- Algorithm analysis (Big O)

**Application in Hospital Project**:
- ✅ **Waiting list queue**: Implement FIFO queue for appointment bookings
- ✅ **Binary search**: Fast patient/doctor lookup by ID or name
- ✅ **Priority queue**: High-priority patients in emergency or lab samples
- ✅ **Hash tables**: Patient/doctor lookup by email (O(1) search)
- ✅ **Tree structures**: Department hierarchy, specialization categories
- ✅ **Sorting**: Sort appointments by date, lab results by patient name
- ✅ **Graph algorithms**: Shortest path for patient referral routing

---

### 2. BIT 202 - Database Management System
**Tech Concepts**:
- Relational model
- SQL queries
- Normalization (1NF to 3NF)
- Transactions, concurrency control
- Indexing, query optimization

**Application in Hospital Project** (CRITICAL):
- ✅ **Database design**:
  - Normalize User, Doctor, Patient, Appointment tables
  - Avoid data redundancy (1NF, 2NF, 3NF)
  - Foreign key relationships
- ✅ **SQL optimization**:
  - Create indexes on frequently queried fields (user_id, appointment_date, doctor_id)
  - Use JOIN queries efficiently (appointments + doctors + patients)
  - Avoid N+1 query problem (use select_related, prefetch_related in Django)
- ✅ **Transactions**: Atomic operations for payment processing
  - Begin transaction → Validate payment → Mark as paid → Send notification → Commit
  - If any step fails, rollback
- ✅ **Concurrency control**: Handle multiple patients booking same time slot simultaneously
  - Use pessimistic locking or optimistic locking
- ✅ **Query optimization**:
  - EXPLAIN ANALYZE to check query plans
  - Aggregate queries for dashboards (COUNT, SUM, AVG)

---

### 3. BIT 203 - Numerical Methods
**Tech Concepts**:
- Root finding algorithms
- Interpolation
- Integration, differentiation
- Error analysis

**Application in Hospital Project**:
- ✅ **Heart risk calculation**: Numerical approximation of Framingham formula
- ✅ **Appointment duration prediction**: Interpolation based on historical data
- ✅ **Payment schedule**: Divide total cost into installments with error correction
- ✅ **Lab result calibration**: Adjust readings based on instrument drift

---

### 4. BIT 204 - Operating System
**Tech Concepts**:
- Process management
- Memory management
- File systems
- Concurrency and synchronization
- Deadlock handling

**Application in Hospital Project**:
- ✅ **Celery workers**: Multiple processes handling tasks (email, SMS, predictions)
- ✅ **Process synchronization**: Redis lock for duplicate appointment prevention
- ✅ **Memory management**: Django cache middleware
- ✅ **File system**: Media storage for patient documents, lab reports, prescriptions (PDF)
- ✅ **Deadlock prevention**: Database transaction isolation levels
- ✅ **Concurrency**: Handle concurrent API requests to prevent race conditions

---

## SEMESTER 4: Web & AI Foundations

### 1. BIT 251 - Web Technology I
**Tech Concepts**:
- HTTP/HTTPS protocols
- Client-server architecture
- HTML, CSS, JavaScript basics
- Web server architecture
- API design (REST)

**Application in Hospital Project** (CORE):
- ✅ **REST API design**: 
  - Endpoints: /api/appointments/, /api/lab/, /api/prescriptions/
  - HTTP methods: GET (retrieve), POST (create), PUT (update), DELETE (remove)
  - Status codes: 200, 201, 400, 403, 404, 500
- ✅ **HTTPS/TLS**:
  - Caddy reverse proxy with automatic TLS
  - All communication encrypted
  - Security headers (HSTS, X-Frame-Options, CSP)
- ✅ **Client-server separation**:
  - Backend: Django REST API
  - Frontend: React/Next.js SPA consuming the API
- ✅ **Session management**: JWT tokens (stateless)
- ✅ **API documentation**: DRF Swagger/OpenAPI schema
- ✅ **CORS policy**: Control which domains can access the API

---

### 2. BIT 252 - Artificial Intelligence
**Tech Concepts**:
- Search algorithms (BFS, DFS, A*)
- Problem-solving techniques
- Knowledge representation
- Game theory, logic

**Application in Hospital Project**:
- ✅ **No-show prediction model**:
  - Train ML model on historical appointment data
  - Features: patient age, doctor, time of day, day of week
  - Output: probability of no-show
- ✅ **Heart risk assessment**:
  - Decision tree or rule-based system
  - Input: patient age, cholesterol, blood pressure
  - Output: risk level (low, medium, high)
- ✅ **Drug interaction checker**:
  - Knowledge base of drug interactions
  - Query: given two drugs, return interaction severity
  - Implement as decision tree or simple lookup table
- ✅ **Patient triage logic**:
  - Rule-based system to assign priority (low, medium, high, critical)
  - Rules: symptoms, vital signs, lab values
- ✅ **Appointment scheduling optimization**:
  - A* search to find best available time for patient

---

### 3. BIT 253 - System Analysis And Design
**Tech Concepts**:
- Requirements gathering
- Data flow diagrams (DFD)
- Entity-relationship diagrams (ERD)
- Use case diagrams
- System design patterns

**Application in Hospital Project**:
- ✅ **ERD (Entity-Relationship Diagram)**:
  ```
  User --1:N-- Appointment
  Doctor --1:N-- Appointment
  Patient --1:N-- Appointment
  Doctor --1:N-- Prescription
  Prescription --1:N-- PrescriptionItem
  Appointment --1:N-- LabTest
  LabTest --1:N-- LabResult
  Patient --1:N-- Review
  ```
- ✅ **Data Flow Diagram**:
  ```
  Patient → Receptionist → Appointment System → Doctor → Prescription → Lab
  Lab → Results → Patient
  Patient → Payment Gateway (Khalti) → Payment System → Verification
  ```
- ✅ **Use cases**:
  - Patient books appointment
  - Doctor completes appointment and prescribes
  - Lab receives test order and enters results
  - Patient views results and pays online
- ✅ **State diagrams**: Appointment states (scheduled → completed → cancelled)

---

### 4. BIT 254 - Network And Data Communications
**Tech Concepts**:
- OSI model
- TCP/IP protocols
- Network topology
- Data transmission
- Network security

**Application in Hospital Project**:
- ✅ **API communication**: HTTP/HTTPS over TCP/IP
- ✅ **Network architecture**:
  - Frontend (port 3000) → Caddy proxy (port 80/443) → Backend (port 8000)
  - Backend → PostgreSQL (port 5432)
  - Backend → Redis (port 6379)
- ✅ **Real-time communication**:
  - WebSockets for live notifications (appointment confirmations, lab results)
  - Fallback: polling if WebSocket not available
- ✅ **Data encryption**: HTTPS for all API calls
- ✅ **Network security**:
  - Firewall rules (only ports 80, 443 open)
  - CORS policy to restrict API access
  - DDoS protection via rate limiting

---

## SEMESTER 5: Software Engineering & Security

### 1. BIT 301 - Web Technology II
**Tech Concepts**:
- Advanced JavaScript/TypeScript
- Frontend frameworks (React, Vue, Angular)
- Server-side rendering vs client-side rendering
- State management
- Frontend testing

**Application in Hospital Project**:
- ✅ **Frontend framework**: React with Next.js
  - Server-side rendering for SEO
  - Client-side state management (Redux/Context)
  - Component-based architecture
- ✅ **Type safety**: TypeScript for frontend
- ✅ **Frontend testing**: Jest, React Testing Library
- ✅ **State management**: Redux for global state (user, notifications, filters)
- ✅ **Form validation**: Client-side and server-side
- ✅ **API integration**: Axios/Fetch with error handling and retry logic

---

### 2. BIT 302 - Software Engineering
**Tech Concepts**:
- SDLC models (Waterfall, Agile, Spiral)
- Project management
- Code quality
- Testing (unit, integration, system)
- Documentation

**Application in Hospital Project**:
- ✅ **Development methodology**:
  - Agile/Scrum: Sprint-based development
  - Version control: Git with branches (main, develop, feature branches)
  - Code review: Pull requests before merge
- ✅ **Testing pyramid**:
  - Unit tests: Test individual functions (40%)
  - Integration tests: Test API endpoints (30%)
  - System tests: Test full workflows (20%)
  - E2E tests: Test UI flows (10%)
- ✅ **CI/CD pipeline**: GitHub Actions
  - Run tests on every commit
  - Auto-deploy to staging on PR merge
  - Manual approval for production
- ✅ **Documentation**:
  - API documentation (Swagger/OpenAPI)
  - README with setup instructions
  - Deployment runbooks
  - Architecture diagrams
- ✅ **Code quality**:
  - Linting: ESLint (frontend), Flake8 (backend)
  - Type checking: MyPy (Python), TypeScript (frontend)
  - Code coverage: Aim for 80%+ coverage

---

### 3. BIT 303 - Information Security
**Tech Concepts**:
- Cryptography (symmetric, asymmetric)
- Authentication and authorization
- Hashing and digital signatures
- SSL/TLS
- Access control, audit trails
- Vulnerability assessment

**Application in Hospital Project** (CRITICAL):
- ✅ **Authentication**:
  - JWT tokens (access + refresh)
  - Secure password hashing: Django's PBKDF2 with salt
  - 2FA (two-factor authentication) via OTP
  - Email verification on registration
- ✅ **Authorization**:
  - Role-based access control (RBAC)
  - Permissions per endpoint
  - Data isolation (patient can only see own records)
- ✅ **Encryption**:
  - HTTPS/TLS for all communication
  - Database credentials in environment variables
  - SECRET_KEY stored securely
  - Sensitive data (SSN, phone) encrypted at rest
- ✅ **Hashing**:
  - Password hashing: PBKDF2, bcrypt, or Argon2
  - Data integrity: HMAC for API responses
- ✅ **Audit trails**:
  - Log all user actions (login, data access, changes)
  - Store logs in immutable format
  - Retention policy: keep for 90 days
- ✅ **OWASP Top 10 protections**:
  - SQL Injection: Use Django ORM with parameterized queries
  - XSS: Sanitize user input, use Content Security Policy
  - CSRF: CSRF tokens on forms
  - Broken authentication: 2FA, strong passwords, rate limiting
  - Sensitive data exposure: HTTPS, encryption, no passwords in logs
  - Insecure deserialization: Validate JSON schema
  - XXE: Disable XML parsing features
  - Broken access control: RBAC on all endpoints
  - Using components with known vulnerabilities: Keep dependencies updated
  - Insufficient logging: Comprehensive audit trails

---

### 4. BIT 304 - Computer Graphics
**Tech Concepts**:
- 2D/3D graphics rendering
- Image processing
- Visualization techniques
- Animation

**Application in Hospital Project**:
- ✅ **Data visualization**:
  - Dashboard charts: Appointment trends, no-show rates, revenue
  - Patient health graphs: Vital signs over time, lab result trends
  - Doctor performance: Rating, appointment count, completion rate
- ✅ **Medical imaging display**:
  - Display lab reports, prescriptions as PDFs
  - Future: DICOM viewer for radiology images
- ✅ **UI/UX animations**:
  - Smooth transitions between pages
  - Loading indicators
  - Success/error notifications with animations
- ✅ **Chart libraries**:
  - Chart.js, D3.js, or Recharts for frontend dashboards
  - Matplotlib/Plotly for Python data visualization (if generating reports server-side)

---

## SEMESTER 6: Distributed Systems & Admin

### 1. BIT 351 - Net-Centric Computing
**Tech Concepts**:
- Distributed systems architecture
- Client-server computing
- Peer-to-peer networks
- Service-oriented architecture (SOA)
- Cloud computing
- Scalability and load balancing

**Application in Hospital Project** (PRODUCTION-CRITICAL):
- ✅ **Distributed architecture**:
  - Backend: Multiple Django instances behind Caddy load balancer
  - Database: PostgreSQL (can be replicated for HA)
  - Cache: Redis cluster for distributed caching
  - Message queue: RabbitMQ or Redis for Celery tasks
- ✅ **Microservices thinking**:
  - Independent services: users, clinical, appointments, lab, etc.
  - API gateway: Caddy (routes requests to appropriate backend)
  - Service discovery: Use environment variables or service mesh (future)
- ✅ **Scalability**:
  - Horizontal scaling: Add more backend containers
  - Vertical scaling: Increase container resources
  - Database sharding: Partition data by patient ID (future)
  - Read replicas: Separate read-only DB for reporting (future)
- ✅ **Load balancing**:
  - Caddy round-robin load balancing
  - Health checks to remove unhealthy backends
  - Sticky sessions for stateful operations
- ✅ **Cloud deployment**:
  - Docker containers for consistency
  - Kubernetes orchestration (future)
  - Auto-scaling based on CPU/memory usage (future)
- ✅ **Reliability**:
  - Redundancy: Multiple backend instances
  - Failover: Automatic switch to healthy backend
  - Data replication: Database backups, replicas
  - Service monitoring: Netdata, health check endpoints

---

### 2. BIT 352 - Database Administration
**Tech Concepts**:
- Database backup and recovery
- Replication and clustering
- Performance tuning
- Capacity planning
- Security and access control

**Application in Hospital Project**:
- ✅ **Backup and recovery**:
  - Daily automated backups (pg_dump)
  - Backup retention: 30 days
  - Restore testing: Practice monthly
  - Backup encryption: Encrypt sensitive backups
  - Offsite backup: Copy to cloud storage (AWS S3, Google Cloud)
- ✅ **Replication**:
  - PostgreSQL replication: Master-replica setup
  - Replica for read-only queries (reporting)
  - Failover to replica if master fails
- ✅ **Performance tuning**:
  - Index optimization: Add indexes on frequently queried columns
  - Query optimization: Use EXPLAIN ANALYZE
  - Connection pooling: PgBouncer to manage connections
  - Caching: Redis for frequently accessed data
  - Partitioning: Split large tables by date or patient ID
- ✅ **Monitoring**:
  - PostgreSQL metrics: Disk usage, connection count, slow queries
  - Alert on high CPU, low disk space, failed backups
  - Query logs: Identify slow queries
- ✅ **Security**:
  - Principle of least privilege: Users with minimal required permissions
  - Role-based access: Admin, read-only, write-only roles
  - Encryption at rest: Transparent data encryption (TDE)
  - Encryption in transit: SSL connections to database
  - Audit: Log schema changes, access patterns
- ✅ **Capacity planning**:
  - Monitor growth rate
  - Plan for storage expansion
  - Estimate backup storage needs

---

### 3. BIT 353 - Management Information System
**Tech Concepts**:
- Business intelligence
- Data warehousing
- OLAP (Online Analytical Processing)
- Data mining
- Executive dashboards
- KPI reporting

**Application in Hospital Project**:
- ✅ **Admin dashboards**:
  - Total patients, doctors, appointments (KPIs)
  - Appointment trends: By date, by doctor, by status
  - No-show rate: Percentage of missed appointments
  - Revenue: Total collected, pending payments
  - Lab volume: Tests ordered, completed, pending
- ✅ **Doctor dashboards**:
  - My patients: List with last appointment
  - My schedule: Today, week, month view
  - My prescriptions: Recently written, pending
  - My reviews: Average rating, recent feedback
- ✅ **Reports**:
  - Daily summary: Appointments, tests, payments
  - Monthly report: KPIs, trends, anomalies
  - Quarterly review: Growth metrics, performance
- ✅ **Data export**:
  - Export to CSV/Excel for external analysis
  - Schedule auto-generated reports (via Celery)
- ✅ **Business rules**:
  - Alert if no-show rate > 10%
  - Alert if payment collection < 80%
  - Alert if lab turnaround time > 24 hours

---

### 4. RSM 354 - Research Methodology
**Tech Concepts**:
- Research design
- Data collection methods
- Statistical analysis
- Hypothesis testing
- Report writing

**Application in Hospital Project**:
- ✅ **User research**:
  - Survey doctors/patients on system usability
  - Identify pain points, feature requests
  - A/B test different UI designs
- ✅ **Data analysis**:
  - Analyze no-show patterns: Which time slots, doctors, patient demographics?
  - Analyze payment patterns: Which methods are most popular?
  - Analyze lab utilization: Peak hours, most ordered tests
- ✅ **Performance measurement**:
  - Measure API response times
  - Measure user satisfaction (NPS, CSAT)
  - Measure system reliability (uptime %)
- ✅ **Documentation**:
  - Document architecture decisions (ADRs)
  - Document lessons learned
  - Publish case study on successful features

---

## Summary: Tech Implementation Priority Map

### Phase 1: MVP (Weeks 1-4) — Database, Security, Auth, Core APIs
```
MUST IMPLEMENT:
✅ Semester 3: BIT 202 - Database design & optimization
✅ Semester 5: BIT 303 - Information security (auth, 2FA, encryption)
✅ Semester 4: BIT 251 - REST API design (appointments, lab, prescriptions)
✅ Semester 2: BIT 153 - OOP design patterns (factories, strategies)
```

### Phase 2: Core Features (Weeks 5-8) — Appointments, Lab, Prescriptions
```
SHOULD IMPLEMENT:
✅ Semester 3: BIT 201 - Data structures (queues for waiting lists)
✅ Semester 3: BIT 204 - OS concepts (concurrency, process management for Celery)
✅ Semester 4: BIT 253 - System design (ERD, DFD, state diagrams)
✅ Semester 5: BIT 301 - Frontend framework (React/Next.js)
```

### Phase 3: AI/ML Features (Weeks 9-10)
```
NICE TO HAVE:
✅ Semester 2: STA 154 - Statistics (heart risk, no-show prediction)
✅ Semester 4: BIT 252 - AI (triage logic, drug interactions)
```

### Phase 4: Production & Scaling (Weeks 11-12)
```
CRITICAL:
✅ Semester 5: BIT 302 - Software engineering (testing, CI/CD, documentation)
✅ Semester 5: BIT 304 - Graphics (dashboards, visualizations)
✅ Semester 6: BIT 351 - Net-centric (load balancing, distributed systems)
✅ Semester 6: BIT 352 - Database admin (backups, replication, monitoring)
✅ Semester 6: BIT 353 - MIS (KPI dashboards, reports)
```

---

## Technology Stack Mapped to BIT Curriculum

| Tech | Course | Semester |
|------|--------|----------|
| Django/REST | BIT 251 (Web I) | 4 |
| PostgreSQL | BIT 202 (DBMS) | 3 |
| Redis | BIT 254 (Networks) | 4 |
| Celery | BIT 204 (OS) | 3 |
| Docker | BIT 101 (IT Intro) | 1 |
| JWT Auth | BIT 303 (Security) | 5 |
| React/Next.js | BIT 301 (Web II) | 5 |
| TypeScript | BIT 301 (Web II) | 5 |
| Scikit-learn | BIT 252 (AI) + STA 154 | 2, 4 |
| Load Balancing | BIT 351 (Net-Centric) | 6 |
| Git/CI-CD | BIT 302 (SE) | 5 |
| Monitoring | BIT 6 (implied) | 6 |

