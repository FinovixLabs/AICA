# Overbuild Control Module

## 1. Purpose

The purpose of this module is to prevent unnecessary overbuilding in the project.

This module must enforce the approved MVP scope and remove unnecessary implementation wherever safe.

It should act as a scope-control layer before building a new module or whenever manually triggered.

---

## 2. Core Objective

The module must:

* Prevent feature creep
* Enforce approved module-specific architecture
* Detect unnecessary implementation
* Detect missing required MVP logic
* Produce a JSON audit output
* Give a hard **YES / NO** verdict
* Automatically fix safe overbuild
* Report risky issues without modifying them
* Stop after fixing safe issues and reporting risky issues

---

## 3. Trigger Points

This module should run:

* Before building a new module
* Manually when specifically requested

It does not need to run automatically after every commit or deployment unless separately configured.

---

## 4. Source of Truth

The module must use the **module-specific architecture file** as the primary source of truth.

Each module must be checked against its own approved architecture and limitations.

Example:

```txt
.claude/modules/filing-module.md
.claude/modules/notice-module.md
.claude/modules/rag-module.md
.claude/modules/ai-output-module.md
```

The overbuild module must not judge a module based on assumptions.
It must compare the implementation only against the approved module-specific architecture file.

---

## 5. Strictness Level

The module should follow a  **balanced strictness level** .

This means:

* Remove clearly unnecessary overbuild
* Keep practical helper logic if it directly supports the MVP
* Do not remove useful implementation only because it is slightly abstracted
* Do not allow future-phase features
* Do not allow unnecessary dashboards, workflows, integrations, or automation
* Do not block simple support utilities if they are required for the module to work properly

---

## 6. Areas to Check

The module should check:

* Backend routes
* Backend services
* AI workflows
* Prompt files
* Validation logic
* Output generation logic
* Configuration files
* Module-level helper functions
* File structure relevant to the module

Frontend checking is not mandatory at this stage because the frontend may have access to many project files.

However, if a frontend file clearly adds an out-of-scope feature, the module may report it.

---

## 7. Database Control Rule

The module must  **never modify database schema files** .

It cannot:

* Delete database tables
* Drop columns
* Modify migration files
* Change Supabase schema definitions
* Change database constraints
* Change RLS policies
* Change database triggers
* Modify production data

If database overbuild is detected, it must only report the issue.

Database-related issues must be marked as risky and sent for manual review.

---

## 8. AI Workflow Control

The module must strictly check AI workflows.

It must flag and prevent AI logic that:

* Gives tax advice beyond the approved scope
* Auto-submits GST filing
* Generates unsupported legal or compliance opinions
* Uses external knowledge without approval
* Invents missing values
* Fills fields without source data
* Bypasses validation
* Ignores the approved module-specific architecture
* Performs tasks assigned to another module

---

## 9. Hard Verdict Rule

Each checked item must receive only one of the following verdicts:

```txt
YES
NO
```

No vague verdicts are allowed.

Do not use:

```txt
MAYBE
OPTIONAL
DEPENDS
RECOMMENDED
MANUAL_REVIEW
```

If an item is risky and cannot be auto-fixed, the verdict should still be  **NO** , but the action should be:

```txt
REPORT_RISK_ONLY
```

---

## 10. Verdict Meaning

| Verdict | Meaning                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------- |
| YES     | Keep or add this item because it is required for the approved module scope                        |
| NO      | Remove, reject, or report this item because it is overbuilt, risky, or outside the approved scope |

---

## 11. Action Types

The module should use these action labels:

```txt
KEEP
ADD
REMOVE
FIXED
REPORT_RISK_ONLY
NO_ACTION
```

### Action Meaning

| Action           | Meaning                                          |
| ---------------- | ------------------------------------------------ |
| KEEP             | Item is valid and should remain                  |
| ADD              | Required MVP item is missing and should be added |
| REMOVE           | Item is overbuilt and should be removed          |
| FIXED            | Safe issue was automatically fixed               |
| REPORT_RISK_ONLY | Risky issue found but not modified               |
| NO_ACTION        | Nothing needs to be changed                      |

---

## 12. Auto-Fix Authority

The module has authority to auto-fix everything except risky database, authentication, security, deployment, and compliance-sensitive changes.

### Auto-fix allowed for:

* Removing unused backend routes
* Removing unused service functions
* Removing duplicate helper functions
* Removing placeholder future features
* Removing unused imports
* Removing unused config flags
* Removing unused mock logic
* Removing future-phase AI workflows
* Removing unnecessary automation
* Adding missing validation checks
* Adding missing error messages
* Adding missing AI grounding rules
* Adding missing JSON output enforcement
* Fixing scope violations in prompt files
* Commenting risky items for manual review where deletion is unsafe

### Auto-fix not allowed for:

* Database schema files
* Supabase migrations
* Authentication logic
* Security logic
* RLS policies
* Environment secrets
* Deployment configuration
* Legal/tax/compliance calculations
* Production data
* Billing records
* Audit records

For these, the module must only report the issue.

---

## 13. Project-Specific Overbuild List

The following features are considered overbuild unless explicitly approved in the relevant module-specific architecture file:

* GST portal submission
* Demand system
* Client billing
* Firm management system
* Advanced analytics
* Auto email reminders
* Mobile app
* WhatsApp integration
* MCA filing
* Payment system
* Multi-tenant SaaS architecture
* Full admin dashboard
* CRM system
* Auto-filing to government portal
* AI tax advisory engine
* Complex role-based access control

If any of these are found, the module must mark them as:

```json
{
  "verdict": "NO",
  "action": "REMOVE"
}
```

If removal is risky, the module must mark them as:

```json
{
  "verdict": "NO",
  "action": "REPORT_RISK_ONLY"
}
```

---

## 14. JSON Output Requirement

The preferred output format is JSON.

The module must return a structured JSON audit report.

### Required JSON Format

```json
{
  "module_reviewed": "module_name",
  "source_of_truth": "path/to/module-architecture.md",
  "final_verdict": "PASS | FAIL | PASS_AFTER_AUTO_FIX",
  "summary": {
    "total_items_checked": 0,
    "items_kept": 0,
    "items_to_add": 0,
    "items_removed_or_fixed": 0,
    "risk_items_reported": 0
  },
  "checklist": [
    {
      "area": "Backend | AI Workflow | Config | Validation | Output | Database | Frontend",
      "item_checked": "item_name_or_description",
      "verdict": "YES | NO",
      "action": "KEEP | ADD | REMOVE | FIXED | REPORT_RISK_ONLY | NO_ACTION",
      "reason": "Clear reason based on module-specific architecture file",
      "file_path": "path/to/file",
      "risk_level": "LOW | MEDIUM | HIGH"
    }
  ],
  "auto_fixes_applied": [
    {
      "file_path": "path/to/file",
      "change_made": "Description of change",
      "reason": "Why it was fixed",
      "status": "FIXED"
    }
  ],
  "risk_items_reported": [
    {
      "file_path": "path/to/file",
      "issue": "Description of risky issue",
      "reason": "Why it cannot be auto-fixed",
      "required_manual_action": "What the developer should review"
    }
  ],
  "items_to_add": [
    {
      "area": "Backend | AI Workflow | Validation | Output | Config",
      "missing_item": "item_name",
      "reason": "Why it is required for MVP",
      "recommended_action": "Add this item"
    }
  ],
  "items_removed": [
    {
      "area": "Backend | AI Workflow | Config | Frontend",
      "removed_item": "item_name",
      "reason": "Why it was overbuilt"
    }
  ],
  "stop_reason": "Safe issues fixed and risky issues reported. Manual review required before continuing."
}
```

---

## 15. Final Verdict Rules

The module must end with one of these final verdicts:

```txt
PASS
```

Use when the module is aligned with the approved module-specific architecture.

```txt
FAIL
```

Use when overbuilt or missing items are found and could not be fully fixed.

```txt
PASS_AFTER_AUTO_FIX
```

Use when overbuilt items were found and safely fixed.

---

## 16. Required Operating Sequence

When triggered, the AI coding agent must follow this sequence:

1. Read the relevant module-specific architecture file.
2. Identify the approved scope and limitations.
3. Scan the current implementation.
4. Compare the implementation against the approved architecture.
5. Identify valid, missing, overbuilt, and risky items.
6. Give every item a hard **YES / NO** verdict.
7. Automatically fix safe issues.
8. Never modify database schema files.
9. Report risky issues separately.
10. Produce the final JSON audit report.
11. Stop after safe fixes and risky issue reporting.

---

## 17. Stop Rule

After the module:

* fixes safe issues,
* reports risky issues,
* and generates the JSON audit,

it must stop.

It must not continue building new features unless the user gives a separate instruction.

---

## 18. Core Principle

Enforce approved MVP code and remove unnecessary implementation.

Do not build beyond the approved module-specific architecture.
