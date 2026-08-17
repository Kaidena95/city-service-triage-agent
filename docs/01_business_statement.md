# Business Statement
## City Service Triage Agent

---

## Problem Statement

The City of Los Angeles receives thousands of service requests
every week across dozens of channels — phone hotlines, email,
walk-in counters, and web portals. Each channel produces
unstructured, free-text descriptions of issues reported by citizens.

This creates three critical operational problems:

**Problem 1 — Inconsistent Classification**
Without a standardized classification system, two staff members
reading the same request may route it to different departments.
A "broken streetlight" might be logged as maintenance by one
person and safety by another, causing duplicate work and delays.

**Problem 2 — No Automatic Prioritization**
Staff must manually assess urgency for every incoming request.
A gas leak and a park bench repair both arrive as plain text
with no urgency signal. Critical issues can sit in a queue
behind routine requests because no system distinguishes them.

**Problem 3 — No Centralized Visibility**
Without a unified dashboard, supervisors cannot see the full
picture of open requests across departments, filter by urgency,
or track resolution rates. Operational decisions are made without
data.

---

## Solution

The City Service Triage Agent is an AI-assisted web application
that standardizes the entire service request intake workflow:

1. **Standardized Intake:** Citizens submit requests through a
   single web form with structured description and location fields.

2. **Automatic Classification:** A rules-based triage classifier
   analyzes each description and assigns a category (maintenance,
   safety, sanitation, facility, IT) and priority level (low,
   medium, high, critical) automatically — no manual review needed
   for routine classification.

3. **Recommended Actions:** The system generates a recommended
   next action for every request based on its category and
   priority — reducing decision load for staff.

4. **Centralized Dashboard:** All requests are visible in a
   real-time dashboard with filter controls for category, priority,
   and status — giving supervisors instant operational visibility.

5. **Live Status Tracking:** Staff can update request status
   (open → in_progress → resolved) directly from the dashboard.

6. **Agentic Interface:** An MCP (Model Context Protocol) server
   exposes all request data and update functions as structured
   tools that AI agents can call — enabling future automation
   of triage workflows.

---

## Business Value

### Quantitative Value

| Metric | Before | After |
|--------|--------|-------|
| Classification time per request | 3-5 minutes manual | < 1 second automated |
| Misrouted requests | Estimated 15-20% | Near 0% for keyword-matching cases |
| Critical request visibility | None | Instant filter by priority=critical |
| Supervisor dashboard | None | Real-time, filter-enabled |

### Qualitative Value

- **Faster emergency response:** Critical safety requests
  (gas leaks, accidents, fires) are automatically flagged as
  critical priority and generate immediate dispatch recommendations
  — reducing time between report and response.

- **Reduced staff cognitive load:** Staff no longer need to
  decide category and priority for every request. The system
  handles routine classification, freeing staff to handle
  exceptions and edge cases.

- **Operational transparency:** Department managers can filter
  the dashboard to see only their department's open requests,
  improving accountability and reducing inter-department
  communication overhead.

- **Agentic readiness:** The MCP layer means this system can
  be connected to an AI agent that autonomously triages, routes,
  and follows up on requests — the foundation for full workflow
  automation.

---

## Target Users

| User | Role | How they use the system |
|------|------|------------------------|
| Citizen | Reporter | Submits service requests via web form |
| Staff member | Triage operator | Views dashboard, updates request status |
| Department manager | Supervisor | Filters dashboard by department, monitors resolution |
| AI agent | Automated operator | Calls MCP tools to query and update requests |

---

## Scope and Limitations

**In scope:**
- Web-based request submission form
- Automatic classification and prioritization
- Dashboard with filters and live status updates
- MCP server with three operational tools
- Rules-based classifier (deterministic, fully explainable)

**Out of scope (future improvements):**
- User authentication and role-based access control
- Email/SMS notifications to citizens on status updates
- LLM-based classifier for edge cases
- Integration with existing city CRM systems
- Mobile native app

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*