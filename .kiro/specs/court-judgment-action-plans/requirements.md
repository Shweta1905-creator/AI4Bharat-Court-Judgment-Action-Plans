# Requirements Document

## Introduction

This document defines the requirements for **Theme 11 — Court Judgments to Verified Action Plans**, developed for the AI for Bharat Hackathon, commissioned by the Centre for e-Governance (Government of India).

The system is an AI-powered pipeline that ingests court judgment PDFs (both digital and scanned), extracts structured legal directives, and presents them to government officers through a Human-in-the-Loop (HiTL) verification dashboard. The output is a verified, structured executive action plan that Nodal Officers and Department Heads can act upon directly.

Manual extraction of directives from court orders is slow, inconsistent, and error-prone. This system eliminates that bottleneck by combining OCR, computer vision preprocessing, and large language model analysis to produce reliable, traceable action plans at scale.

---

## Glossary

- **System**: The end-to-end AI pipeline and dashboard described in this document.
- **Document_Ingestion_Service**: The component responsible for receiving uploaded PDF files and storing them for processing.
- **Preprocessing_Engine**: The component that applies image correction (deskewing, denoising, contrast enhancement) to scanned PDF pages using OpenCV before OCR.
- **OCR_Engine**: The component that performs optical character recognition on document images using AWS Textract.
- **Directive_Extractor**: The AI component powered by Amazon Bedrock (Claude 3) that identifies and structures legal directives from extracted text.
- **Action_Plan**: A structured, machine-readable document containing one or more Directives extracted from a court judgment.
- **Directive**: A single actionable instruction extracted from a court order, comprising an order description, deadline (if present), responsible party, and compliance status.
- **Verification_Dashboard**: The Streamlit-based web interface through which Nodal Officers and Department Heads review, edit, approve, or reject extracted Directives.
- **Nodal_Officer**: A government official responsible for reviewing and approving Action Plans generated from court judgments assigned to their department.
- **Department_Head**: A senior government official who has final approval authority over verified Action Plans.
- **Storage_Service**: Amazon S3, used to store uploaded PDFs, intermediate artifacts, and final Action Plans.
- **Processing_Trigger**: An AWS Lambda function that initiates the processing pipeline upon document upload.
- **Audit_Log**: An immutable, timestamped record of all system actions, user decisions, and document state transitions.
- **Confidence_Score**: A numeric value (0.0–1.0) assigned by the Directive_Extractor indicating its certainty in a given extraction.

---

## Requirements

### Requirement 1: Document Upload and Storage

**User Story:** As a Nodal Officer, I want to upload court judgment PDFs through the dashboard, so that the system can process them without requiring manual file transfers or technical intervention.

#### Acceptance Criteria

1. THE Verification_Dashboard SHALL provide a file upload interface that accepts PDF files up to 100 MB in size.
2. WHEN a PDF file is uploaded, THE Document_Ingestion_Service SHALL store the file in the Storage_Service within 10 seconds of upload completion.
3. IF a file exceeding 100 MB is uploaded, THEN THE Document_Ingestion_Service SHALL reject the upload and return a descriptive error message to the user.
4. IF a file with a MIME type other than `application/pdf` is uploaded, THEN THE Document_Ingestion_Service SHALL reject the upload and return a descriptive error message to the user.
5. WHEN a PDF is successfully stored, THE Document_Ingestion_Service SHALL assign a unique document identifier and record the upload timestamp in the Audit_Log.

---

### Requirement 2: Image Preprocessing for Scanned Documents

**User Story:** As a Nodal Officer, I want the system to handle scanned court documents, so that poor scan quality does not prevent accurate text extraction.

#### Acceptance Criteria

1. WHEN a PDF page is identified as a scanned image (non-selectable text), THE Preprocessing_Engine SHALL apply deskewing, denoising, and contrast normalisation to the page image before passing it to the OCR_Engine.
2. THE Preprocessing_Engine SHALL process each page of a document independently, so that a low-quality page does not block processing of other pages.
3. WHEN preprocessing of a page fails, THE Preprocessing_Engine SHALL log the failure with the page number and document identifier in the Audit_Log and continue processing remaining pages.
4. THE Preprocessing_Engine SHALL produce output images at a minimum resolution of 300 DPI to ensure OCR accuracy.

---

### Requirement 3: Optical Character Recognition

**User Story:** As a Nodal Officer, I want the system to accurately extract text from court documents, so that the AI analysis is based on complete and correct document content.

#### Acceptance Criteria

1. WHEN a preprocessed page image is available, THE OCR_Engine SHALL submit it to AWS Textract and retrieve the extracted text with positional metadata.
2. THE OCR_Engine SHALL preserve the reading order of extracted text blocks as determined by AWS Textract's layout analysis.
3. WHEN AWS Textract returns a confidence score below 0.80 for a text block, THE OCR_Engine SHALL flag that block and include the flag in the document's processing record.
4. IF the AWS Textract service is unavailable, THEN THE OCR_Engine SHALL retry the request up to 3 times with exponential backoff before marking the document as failed and notifying the Nodal_Officer.
5. WHEN OCR processing for a document is complete, THE OCR_Engine SHALL store the full extracted text in the Storage_Service and update the document state in the Audit_Log.

---

### Requirement 4: Legal Directive Extraction

**User Story:** As a Nodal Officer, I want the system to automatically identify actionable directives from court text, so that I do not have to read the entire judgment to find compliance obligations.

#### Acceptance Criteria

1. WHEN extracted text for a document is available, THE Directive_Extractor SHALL submit the text to Amazon Bedrock (Claude 3) with a structured prompt designed to identify legal directives.
2. THE Directive_Extractor SHALL extract the following fields for each identified Directive: order description, deadline (date or duration, if stated), responsible party (individual, department, or entity), and directive category (e.g., compliance, reporting, payment).
3. WHERE a deadline is not explicitly stated in the judgment text, THE Directive_Extractor SHALL set the deadline field to `null` and record the absence in the Directive.
4. THE Directive_Extractor SHALL assign a Confidence_Score between 0.0 and 1.0 to each extracted Directive.
5. WHEN extraction is complete, THE Directive_Extractor SHALL produce a structured Action_Plan in JSON format and store it in the Storage_Service.
6. IF the Amazon Bedrock service returns an error, THEN THE Directive_Extractor SHALL retry the request up to 3 times with exponential backoff before marking the document as failed and notifying the Nodal_Officer.
7. THE Directive_Extractor SHALL not hallucinate directives; all extracted Directives SHALL be traceable to a specific passage in the source document text, identified by page number and character offset.

---

### Requirement 5: Human-in-the-Loop Verification

**User Story:** As a Nodal Officer, I want to review, edit, and approve extracted directives before they become official action plans, so that errors in AI extraction do not propagate into government compliance records.

#### Acceptance Criteria

1. WHEN an Action_Plan is available, THE Verification_Dashboard SHALL display all extracted Directives to the Nodal_Officer in a structured, tabular view showing order description, deadline, responsible party, category, and Confidence_Score.
2. THE Verification_Dashboard SHALL allow the Nodal_Officer to edit the order description, deadline, responsible party, and category fields of any Directive inline.
3. THE Verification_Dashboard SHALL allow the Nodal_Officer to delete a Directive that is identified as incorrectly extracted.
4. THE Verification_Dashboard SHALL allow the Nodal_Officer to add a new Directive manually if the AI extraction missed an obligation.
5. WHEN a Nodal_Officer submits a verified Action_Plan, THE Verification_Dashboard SHALL record the officer's identity, the timestamp, and all edits made in the Audit_Log before updating the Action_Plan status to `verified`.
6. WHILE an Action_Plan has status `verified`, THE System SHALL prevent further edits unless the Nodal_Officer explicitly unlocks the record, which SHALL be recorded in the Audit_Log.
7. WHERE a Directive has a Confidence_Score below 0.60, THE Verification_Dashboard SHALL visually highlight the Directive to draw the Nodal_Officer's attention.

---

### Requirement 6: Action Plan Approval by Department Head

**User Story:** As a Department Head, I want to perform a final review and approve verified action plans, so that only authorised, reviewed plans are used for compliance tracking.

#### Acceptance Criteria

1. WHEN an Action_Plan status is `verified`, THE Verification_Dashboard SHALL make the Action_Plan available to the Department_Head for final approval.
2. THE Verification_Dashboard SHALL allow the Department_Head to approve or reject a verified Action_Plan with a mandatory comment field.
3. WHEN a Department_Head approves an Action_Plan, THE System SHALL update the Action_Plan status to `approved` and record the approval in the Audit_Log with the officer's identity and timestamp.
4. WHEN a Department_Head rejects an Action_Plan, THE System SHALL update the Action_Plan status to `rejected`, record the rejection reason in the Audit_Log, and notify the Nodal_Officer.
5. WHEN an Action_Plan is rejected, THE Verification_Dashboard SHALL allow the Nodal_Officer to revise and resubmit the Action_Plan for re-verification.

---

### Requirement 7: Action Plan Export

**User Story:** As a Nodal Officer, I want to export approved action plans in standard formats, so that they can be shared with relevant departments and integrated into existing government workflows.

#### Acceptance Criteria

1. WHEN an Action_Plan has status `approved`, THE Verification_Dashboard SHALL provide options to export the Action_Plan as a PDF report and as a structured JSON file.
2. THE Verification_Dashboard SHALL generate the PDF export with a standardised government report template including document title, case reference, extraction date, approval details, and a table of all Directives.
3. WHEN an export is generated, THE System SHALL store a copy of the exported file in the Storage_Service and record the export event in the Audit_Log.

---

### Requirement 8: Processing Pipeline Orchestration

**User Story:** As a system administrator, I want document processing to be triggered automatically upon upload, so that Nodal Officers do not need to manually initiate each processing step.

#### Acceptance Criteria

1. WHEN a PDF is stored in the Storage_Service, THE Processing_Trigger SHALL automatically invoke the processing pipeline comprising the Preprocessing_Engine, OCR_Engine, and Directive_Extractor in sequence.
2. THE Processing_Trigger SHALL pass the document identifier and Storage_Service object key to each pipeline stage.
3. WHEN any pipeline stage fails after exhausting retries, THE Processing_Trigger SHALL update the document status to `failed`, record the failure details in the Audit_Log, and notify the Nodal_Officer.
4. THE Verification_Dashboard SHALL display the real-time processing status of each uploaded document (e.g., `uploaded`, `preprocessing`, `ocr_in_progress`, `extracting`, `pending_review`, `verified`, `approved`, `failed`).

---

### Requirement 9: Audit Trail and Traceability

**User Story:** As a Department Head, I want a complete audit trail of all actions taken on a court judgment, so that the system meets government accountability and compliance standards.

#### Acceptance Criteria

1. THE System SHALL record every state transition of a document in the Audit_Log with the actor identity, action type, timestamp, and previous and new state values.
2. THE System SHALL record every edit made to a Directive during verification in the Audit_Log, including the field name, previous value, and new value.
3. THE Verification_Dashboard SHALL provide a read-only audit trail view for each document, accessible to both Nodal_Officers and Department_Heads.
4. THE Audit_Log SHALL be immutable; no user role SHALL have the ability to delete or modify Audit_Log entries through the Verification_Dashboard.
5. WHEN an Action_Plan is exported, THE System SHALL include the document's Audit_Log summary in the PDF export.

---

### Requirement 10: Security and Access Control

**User Story:** As a system administrator, I want role-based access control enforced across the system, so that sensitive court documents and action plans are accessible only to authorised personnel.

#### Acceptance Criteria

1. THE System SHALL enforce role-based access control with at minimum two roles: `nodal_officer` and `department_head`.
2. WHEN a user attempts to access a document or Action_Plan, THE System SHALL verify the user's role and department assignment before granting access.
3. IF a user attempts to perform an action not permitted by their role, THEN THE System SHALL deny the action and record the unauthorised attempt in the Audit_Log.
4. THE System SHALL authenticate all users before granting access to the Verification_Dashboard.
5. WHILE a document is in transit between system components, THE System SHALL transmit data exclusively over encrypted channels (TLS 1.2 or higher).
