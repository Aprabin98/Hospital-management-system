# Individual Report: CASE Tools in Software Project Management

## Project: Hospital Management System

**Subject:** Software Project Management  
**Prepared individually for:** Semester project submission  
**Project type:** Full-stack Hospital Management System using Django and Next.js

## Abstract

This report explains how Computer-Aided Software Engineering (CASE) tools support the software project management activities of a semester-based Hospital Management System project. The report focuses on five important areas requested in the assignment: project management, scheduling, estimation, software configuration management, and risk management. The hospital project is a strong example because it contains many connected modules such as user authentication, appointments, clinical records, laboratory workflow, payments, prescriptions, notifications, and audit logging. CASE tools help manage this complexity by improving visibility, control, traceability, and delivery quality throughout the project life cycle.

## 1. Introduction

CASE tools are software tools that assist engineers and managers during planning, analysis, design, coding, testing, deployment, and maintenance. In modern projects, they are often used as integrated toolchains rather than as isolated tools. For a hospital management system, CASE tools are especially useful because the project includes multiple stakeholders, strict security requirements, database-driven workflows, and many dependent modules.

In software project management, CASE tools reduce manual effort and improve decision-making in the following ways:

- they help track project tasks and milestones,
- they support schedule creation and monitoring,
- they provide methods for effort and cost estimation,
- they maintain code and document versions,
- they identify and monitor project risks.

## 2. Project Overview

The chosen project for this report is a Hospital Management System built as a full-stack web application. Based on the current codebase, the project includes the following main areas:

- authentication and role-based access control,
- patient and user management,
- appointment booking and queue management,
- clinical records and diagnoses,
- laboratory bookings and test results,
- prescriptions and pharmacy-related workflows,
- payments, invoices, and billing,
- notifications through email or SMS,
- audit logs and compliance tracking,
- deployment support with Docker, PostgreSQL, Redis, and Caddy.

This project is suitable for a CASE-tool report because it combines frontend, backend, database, and operational concerns. Each module can be planned, scheduled, estimated, version-controlled, and risk-managed separately while still being integrated into one product.

## 3. CASE Tools for Project Management

Project management CASE tools help the team organize work, assign responsibilities, track progress, and monitor delivery. They are used to convert a broad project vision into smaller manageable tasks.

### Common tools

- Jira
- Trello
- ClickUp
- Monday.com
- OpenProject

### Use in this project

For the Hospital Management System, a project management tool can be used to create epics for major modules such as appointments, clinical records, billing, and notifications. Each epic can then be broken into user stories and tasks.

Example uses:

- creating a backlog for each module,
- assigning tasks to frontend, backend, and testing work,
- tracking progress with Kanban or Scrum boards,
- recording blockers and dependencies,
- generating reports for completed and pending work.

### Why it matters

The project contains several interdependent modules. For example, appointment booking depends on user authentication, doctor availability, and notification services. A project management CASE tool makes these dependencies visible and helps the team avoid duplicated effort or missed tasks.

## 4. CASE Tools for Scheduling

Scheduling CASE tools are used to create timelines, define task dependencies, and monitor whether the project is on time. They are especially useful in semester projects where delivery has a fixed deadline.

### Common tools

- Microsoft Project
- GanttProject
- OpenProject
- TeamGantt
- ClickUp Gantt view

### Sample semester schedule for this project

| Week | Main Activity | Typical Output |
|---|---|---|
| 1-2 | Requirement analysis and scope finalization | Requirements list, module list, and constraints |
| 3-4 | UI wireframes and architecture planning | Initial design and database plan |
| 5-6 | Backend development | Core APIs, models, authentication, and permissions |
| 6-8 | Frontend development | Pages, forms, dashboards, and API integration |
| 8-9 | Database and workflow integration | Working end-to-end module flow |
| 10 | Testing and bug fixing | Test results and defect corrections |
| 11 | Documentation and report writing | User guide, technical notes, and final report |
| 12 | Deployment and final presentation | Release build and demonstration |

### How scheduling tools help

Scheduling tools can show task dependencies such as:

- database schema must be ready before most backend features,
- backend APIs must be stable before frontend integration,
- testing should start as soon as the first workflows are complete,
- deployment should happen after system-level verification.

For this project, a Gantt chart is useful because it shows the overlap between backend and frontend work and makes it easier to manage the semester deadline.

## 5. CASE Tools for Estimation

Estimation tools help predict project size, effort, duration, and cost. In software project management, estimation is important because it supports realistic planning and prevents over-commitment.

### Common estimation approaches and tools

- COCOMO II calculators,
- Function Point Analysis tools,
- story-point estimation in agile tools such as Jira,
- spreadsheet-based estimation models,
- expert judgment supported by historical data.

### Estimation approach for this project

For a semester project like the Hospital Management System, a practical approach is to estimate effort by module. Each module can be assigned a relative size and then converted into person-hours or story points.

| Module | Relative Complexity | Example Effort |
|---|---|---|
| Authentication and roles | Medium | 40-60 hours |
| Appointments and scheduling | High | 60-90 hours |
| Clinical records and diagnoses | High | 70-100 hours |
| Laboratory workflow | Medium | 50-70 hours |
| Billing and payments | Medium | 50-80 hours |
| Notifications and audit | Medium | 40-60 hours |
| Frontend integration and testing | High | 80-120 hours |

### Illustrative function point view

An illustrative function point breakdown for the project could be:

- authentication and role handling,
- appointment creation and management,
- clinical record entry and retrieval,
- lab test booking and result release,
- payment and invoice processing,
- notification and audit logging.

This type of estimation helps compare modules and estimate whether the semester timeline is realistic. The main value is not exact arithmetic but better planning and visibility.

## 6. CASE Tools for Software Configuration Management

Software Configuration Management (SCM) is the discipline of controlling changes in source code, documents, databases, build scripts, and deployment assets. For a full-stack application, SCM is essential because the backend, frontend, database migrations, and deployment files all change over time.

### Common SCM tools

- Git,
- GitHub,
- GitLab,
- Bitbucket,
- Subversion,
- Azure DevOps.

### SCM practices for this project

Recommended SCM practices for the Hospital Management System include:

- using a main branch for stable code,
- using feature branches for each module,
- creating pull requests for review,
- tagging releases for milestones,
- storing Django migrations in version control,
- tracking dependency files such as requirements and package manifests,
- excluding generated files and local environment files from the repository.

### Why SCM is important here

This project has multiple moving parts:

- backend services built with Django,
- frontend pages built with Next.js,
- database changes through migrations,
- scripts for maintenance and deployment.

Without SCM, it would be difficult to know which version of the application was used for a demo, which changes caused a bug, or which migration introduced a schema issue. SCM tools provide traceability and rollback support.

## 7. CASE Tools for Risk Management

Risk management tools help identify possible problems early and define mitigation strategies. In software projects, risk management is not optional because delays, integration failures, or security problems can affect the final quality of the system.

### Common tools and techniques

- Risk register in Jira or OpenProject,
- risk matrix in spreadsheets,
- Active Risk Manager,
- RiskyProject,
- Monte Carlo-based schedule risk analysis,
- issue tracking with severity and priority labels.

### Sample risk register for this project

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| API and frontend integration mismatch | Medium | High | Define API contracts early and test endpoints incrementally |
| Database migration error | Medium | High | Use versioned migrations and keep backups |
| Authentication or permission bug | Medium | High | Review role-based access logic and add tests |
| Scope creep | High | Medium | Freeze semester scope after requirement analysis |
| Deployment configuration failure | Medium | High | Test Docker and environment settings before final demo |
| Data privacy issue | Low to Medium | High | Limit access by role and audit sensitive actions |

### How CASE tools help with risk control

CASE-based risk tools help the team record risks, assign owners, set review dates, and monitor mitigation progress. In a hospital system, this is important because incorrect access control or lost data can have serious consequences.

## 8. Practical Mapping of CASE Tools to This Project

The table below shows how the different CASE tool categories support the project life cycle.

| Project Activity | CASE Tool Category | Example Tool |
|---|---|---|
| Planning and task tracking | Project management | Jira, Trello |
| Timeline creation | Scheduling | Microsoft Project, GanttProject |
| Effort prediction | Estimation | COCOMO II, Function Point tools |
| Source control and release control | SCM | Git, GitHub |
| Problem and uncertainty tracking | Risk management | Jira risk board, RiskyProject |

This mapping shows that CASE tools are not used only at the end of the project. They support the entire software life cycle from planning to delivery.

## 9. Conclusion

The Hospital Management System is a suitable semester project for studying software project management because it includes multiple modules, changing requirements, and strong integration needs. CASE tools help the project in five major ways: they improve project management, make scheduling visible, support realistic estimation, control configuration changes, and reduce risks.

In this project, a practical combination of Jira or Trello for task management, GanttProject or Microsoft Project for scheduling, COCOMO II or function point analysis for estimation, Git and GitHub for SCM, and a risk register for risk tracking would provide strong support. Together, these tools improve visibility, accountability, and delivery quality, which are all essential for successful software project management.

## 10. References

- Atlassian Jira documentation
- Microsoft Project documentation
- GanttProject documentation
- COCOMO II estimation model references
- Git documentation
- Standard software project management and CASE tool textbooks
