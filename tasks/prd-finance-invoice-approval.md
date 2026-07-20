# PRD: Finance Invoice Approval Platform

## 1. Introduction/Overview

Employees currently have no self-service way to submit invoice reimbursement requests with supporting documentation, and the finance team has no centralized way to review, approve, reject, or request more information on these requests. This leads to email-based back-and-forth, lost documents, and no visibility into request status for either party.

This feature introduces a web-based Finance Invoice Approval Platform where:
- Employees ("Requesters") submit reimbursement requests with supporting documents and track their status.
- The Finance team reviews all requests, approves/rejects/requests-more-info, and has full visibility into historic and pending requests across all users.

## 2. Goals

- Allow any employee to submit an invoice reimbursement request with supporting documents in under 2 minutes.
- Automatically notify the finance team by email whenever a new request is submitted.
- Give the finance team a single dashboard to see all pending and historic requests across all users.
- Allow the finance team to approve, reject, or request more information (with a reason) on any request.
- Allow requesters to see the real-time status of all their own requests without contacting finance directly.
- Ensure every status change is auditable (who changed it, when, and why).

## 3. User Stories

### US-001: User registration and login
**Description:** As an employee, I want to create an account and log in with email/password so that my requests are tied to my identity.

**Acceptance Criteria:**
- [ ] User can sign up with name, email, and password
- [ ] Passwords are hashed (never stored in plaintext) and validated for minimum strength
- [ ] User can log in and receive a session (e.g. JWT or session cookie)
- [ ] User can log out
- [ ] Invalid login attempts show a clear error message without revealing whether the email exists
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-002: Finance team role assignment
**Description:** As a system, I need to distinguish "Requester" users from "Finance" users so that permissions are enforced correctly.

**Acceptance Criteria:**
- [ ] User accounts have a `role` field: `requester` or `finance`
- [ ] New signups default to `requester`
- [ ] Finance role can only be assigned via direct database update or an admin-only mechanism (no self-service promotion to finance for MVP)
- [ ] Finance-only pages/API routes reject non-finance users with a 403
- [ ] Typecheck/lint passes

### US-003: Submit a new reimbursement request
**Description:** As a requester, I want to submit an invoice reimbursement request with amount, description, expense date, category, and supporting documents so that finance can review it.

**Acceptance Criteria:**
- [ ] Form captures: amount, currency (default a single fixed currency, e.g. USD), expense category (dropdown: e.g. Travel, Meals, Supplies, Software, Other), expense date, description, and requester info (auto-filled from logged-in user)
- [ ] Form allows uploading one or more supporting documents (PDF, JPG, PNG; max file size and count enforced, e.g. 10MB/file, 5 files)
- [ ] Client-side validation prevents submission with missing required fields or invalid file types
- [ ] On submit, a new record is inserted into the database with status `pending`
- [ ] Uploaded files are stored on local disk under a request-specific path, with file metadata (original name, size, path) saved in the database
- [ ] On successful submission, an email is sent to the finance team distribution address with request summary and a link to review it
- [ ] User sees a confirmation message/screen after submission with the new request's ID/status
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-004: Requester views their own request list and status
**Description:** As a requester, I want to see a list of all my submitted requests and their current status so that I know what's pending, approved, or rejected.

**Acceptance Criteria:**
- [ ] "My Requests" page lists all requests submitted by the logged-in user only
- [ ] Each row shows: date submitted, amount, category, description (truncated), current status (Pending / Approved / Rejected / More Info Needed), last updated date
- [ ] List is sorted by most recently updated first
- [ ] Clicking a request opens a detail view showing full details, uploaded documents (downloadable), and full status history with finance's reasons/comments
- [ ] Empty state message shown when user has no requests yet
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-005: Finance dashboard — pending requests
**Description:** As a finance team member, I want to see all pending requests from all users in one place so that I can review and act on them.

**Acceptance Criteria:**
- [ ] "Pending Requests" view accessible only to finance-role users
- [ ] Lists all requests with status `pending` or `more_info_needed`, across all requesters
- [ ] Each row shows: requester name/email, date submitted, amount, category, description (truncated), status
- [ ] List is sortable/filterable by requester, category, and date submitted
- [ ] Clicking a request opens the detail/review view (see US-006)
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-006: Finance approves, rejects, or requests more info
**Description:** As a finance team member, I want to approve, reject, or request more information on a request (with a reason/comment) so that the requester knows the outcome and any next steps.

**Acceptance Criteria:**
- [ ] Request detail view shows all submitted fields and uploaded documents (viewable/downloadable)
- [ ] Finance user can select one of three actions: Approve, Reject, Request More Info
- [ ] Reject and Request More Info require a mandatory free-text reason/comment; Approve allows an optional comment
- [ ] Submitting an action updates the request's status and appends an entry to the status history log (status, reason, finance user who acted, timestamp)
- [ ] An email notification is sent to the requester informing them of the new status and reason/comment
- [ ] If status is set to "More Info Needed", the requester can add additional documents and/or an updated description to the same request and resubmit it for review (status reverts to `pending`)
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-007: Finance views all historic requests
**Description:** As a finance team member, I want to see all requests (regardless of status) across all users so that I have a complete audit trail.

**Acceptance Criteria:**
- [ ] "All Requests" view accessible only to finance-role users, shows requests of every status (Pending, Approved, Rejected, More Info Needed)
- [ ] Filterable by requester, status, category, and date range
- [ ] Each row links to the full detail view including complete status history
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-008: Email notifications
**Description:** As a system, I need to send email notifications at key workflow events so that users and finance stay informed without checking the UI constantly.

**Acceptance Criteria:**
- [ ] Email sent to finance distribution address on new request submission (includes requester, amount, category, link to request)
- [ ] Email sent to requester on any status change (Approved / Rejected / More Info Needed), including finance's reason/comment
- [ ] Emails sent via SMTP using configurable environment variables (host, port, credentials, from-address)
- [ ] Email sending failures are logged but do not block the underlying database transaction (e.g. request submission still succeeds even if the email fails)
- [ ] Typecheck/lint passes

## 4. Functional Requirements

- FR-1: The system must allow users to sign up and log in with email/password authentication.
- FR-2: The system must assign each user a role of `requester` or `finance`, defaulting to `requester`.
- FR-3: The system must provide a form for requesters to submit a reimbursement request with amount, currency, category, expense date, description, and one or more supporting document uploads.
- FR-4: The system must validate uploaded file types (PDF/JPG/PNG) and size (max 10MB per file, max 5 files per request) before accepting them.
- FR-5: On submission, the system must insert the request and its documents into the database with status `pending`.
- FR-6: On submission, the system must send an email to the finance team distribution address summarizing the request.
- FR-7: The system must allow finance-role users to view all pending/more-info-needed requests across all users.
- FR-8: The system must allow finance-role users to view all requests regardless of status ("All Requests" / historic view), with filters by requester, status, category, and date range.
- FR-9: The system must allow finance-role users to approve, reject, or request more info on a request, requiring a reason/comment for reject and request-more-info actions.
- FR-10: Each status change must be recorded in a status history log with the acting finance user, timestamp, new status, and reason/comment.
- FR-11: When a request's status changes, the system must send an email to the requester with the new status and reason/comment.
- FR-12: When a request is marked "More Info Needed," the requester must be able to update the request (add documents, edit description) and resubmit it, reverting status to `pending`.
- FR-13: The system must allow requesters to view a list of only their own submitted requests and each request's current status and full history.
- FR-14: The system must restrict finance-only views and actions (dashboards, approve/reject/request-info) to users with the `finance` role, returning a 403 for unauthorized access attempts.
- FR-15: The system must store uploaded documents on local disk with file metadata (name, size, path, associated request ID) persisted in the database.

## 5. Non-Goals (Out of Scope)

- Multi-stage/hierarchical approval workflows (e.g. manager approval before finance) — single-stage finance approval only.
- SSO/enterprise identity provider integration — MVP uses simple email/password only.
- Multi-currency conversion or exchange-rate handling — a single fixed currency is used.
- In-app real-time notifications (websockets/push) — email is the only notification channel for MVP.
- Payment processing or integration with accounting/ERP systems (e.g. actually issuing reimbursement payments).
- Mobile native apps — web-only, responsive design is sufficient.
- Cloud file storage (S3, etc.) — local disk storage only for MVP.
- Reporting/analytics dashboards beyond basic filtering (e.g. no spend-by-category charts).
- Self-service role promotion to `finance` — role assignment is a manual/admin action only.

## 6. Design Considerations

- Clean, modern, "decent" UI — use a simple component library (e.g. MUI or Tailwind + headless UI) to move quickly while looking professional.
- Two primary navigation contexts: a Requester view (My Requests, New Request) and a Finance view (Pending, All Requests), shown based on logged-in user's role.
- Status should be visually distinct via colored badges: Pending (yellow/amber), Approved (green), Rejected (red), More Info Needed (blue/orange).
- Request detail view should be a single consistent component reused across both the requester's "My Requests" detail and finance's review screens, with action buttons (Approve/Reject/Request Info) conditionally shown only for finance.
- Forms should show inline validation errors before submission.

## 7. Technical Considerations

- **Frontend:** React (SPA).
- **Backend:** Python, FastAPI framework.
- **Database:** PostgreSQL. Core tables: `users` (id, name, email, password_hash, role), `requests` (id, requester_id, amount, currency, category, expense_date, description, status, created_at, updated_at), `request_documents` (id, request_id, file_name, file_path, file_size, uploaded_at), `request_status_history` (id, request_id, status, reason, changed_by_user_id, changed_at).
- **Authentication:** Password hashing via a standard library (e.g. bcrypt/passlib); session via JWT.
- **Email:** SMTP via Python's `smtplib`/`email` or a library like `fastapi-mail`, configured via environment variables (host, port, username, password, from-address, finance distribution address).
- **File storage:** Local disk, organized by request ID (e.g. `/uploads/{request_id}/{filename}`), with size/type validation enforced server-side (not just client-side).
- **API design:** RESTful JSON API between React frontend and FastAPI backend, with role-based access control middleware/dependencies protecting finance-only routes.
- Environment configuration (DB connection string, SMTP settings, upload directory, file size limits) should be externalized via `.env`/environment variables, not hardcoded.

## 8. Success Metrics

- 100% of new reimbursement requests result in a finance notification email being sent within seconds of submission.
- Requesters can determine their request status without contacting finance directly (measured via reduced status-check emails/Slack messages, if trackable).
- Finance team can process (approve/reject/request-info) a request in under 2 minutes using the dashboard.
- Zero data loss: every submitted document and status change is retrievable via the UI.

## 9. Open Questions

- Should there be a maximum request amount or category-specific rules (e.g. amounts over $500 require additional justification)? Currently out of scope but may be a future enhancement.
- What is the finance team's email distribution address / how is it configured (single mailbox vs. multiple finance user emails)?
- Should rejected/more-info requests be editable indefinitely, or is there a resubmission deadline?
- Is there a need for a password reset ("forgot password") flow in the MVP, or can that be deferred?
- Should there be pagination/infinite scroll for the "All Requests" historic view once volume grows, and at what threshold?
