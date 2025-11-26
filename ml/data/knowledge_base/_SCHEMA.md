# DHRUVA Knowledge Base - Schema Documentation

**Version:** 1.0
**Created:** 2025-11-25
**Purpose:** Comprehensive schema definitions for all JSON files in the knowledge base

---

## Table of Contents
1. [Tier 1 Core Schemas](#tier-1-core-schemas)
2. [Tier 2 Training Schemas](#tier-2-training-schemas)
3. [Tier 3 Reference Schemas](#tier-3-reference-schemas)
4. [Tier 4 Audit Schemas](#tier-4-audit-schemas)
5. [Common Field Types](#common-field-types)
6. [Validation Rules](#validation-rules)

---

## Tier 1 Core Schemas

### DepartmentSchema
**File:** `tier1_core/departments.json`
**Usage:** Department classification, routing, keyword matching

```typescript
interface Department {
  id: number;                      // Unique ID (1-30)
  name_english: string;            // Official English name
  name_telugu: string;             // Telugu name (UTF-8)
  code: string;                    // 3-4 letter department code (e.g., "REV", "MAUD")
  priority_rank: number;           // Priority ranking (1=highest, 31=lowest)
  typical_volume_pct: number;      // Expected percentage of total grievances (0-100)
  subdepartments: string[];        // List of sub-department names
  hod: string;                     // Head of Department designation
  keywords_english: string[];      // English keywords for classification (10-100 per dept)
  keywords_telugu: string[];       // Telugu keywords for classification (10-100 per dept)
  common_subjects: string[];       // Frequent subject areas (3-10 per dept)
}

interface DepartmentFile {
  _metadata: {
    created: string;               // ISO date "YYYY-MM-DD"
    version: string;               // Semantic version "X.Y"
    description: string;
    _source: string[];             // Source file paths
    total_departments: number;
    total_subdepartments: number;
    total_keywords: number;
    schema: "DepartmentSchema";
  };
  departments: Department[];
  usage_notes: {
    classification: string;
    multilingual: string;
    search: string;
    training: string;
    priority: string;
    volume: string;
  };
}
```

**Validation Rules:**
- `id`: Must be unique, 1-30
- `name_english`, `name_telugu`: Required, non-empty
- `code`: 2-5 uppercase letters
- `priority_rank`: 1-31
- `typical_volume_pct`: 0.0-100.0
- `keywords_english`, `keywords_telugu`: Must have equal or similar counts
- All Telugu text must be valid UTF-8 (U+0C00 to U+0C7F)

---

### GrievanceTypeSchema
**File:** `tier1_core/grievance_types.json`
**Usage:** Distress level detection, SLA calculation, sentiment analysis

```typescript
interface DistressLevel {
  level: "CRITICAL" | "HIGH" | "MEDIUM" | "NORMAL";
  value: 1 | 2 | 3 | 4;           // Numeric value for comparison
  description: string;             // Plain English description
  telugu: string;                  // Telugu translation
  examples: string[];              // Telugu word examples (3-6)
  keywords_english: string[];      // Detection keywords in English (8-12)
  keywords_telugu: string[];       // Detection keywords in Telugu (8-12)
  sla_hours: 24 | 72 | 168 | 336; // Service Level Agreement in hours
  frequency_pct: number;           // Percentage of grievances in this level
}

interface GrievanceType {
  type: string;                    // Type name in English
  telugu: string;                  // Telugu translation
  description: string;             // Detailed description
  department_prevalence: string[]; // Departments where this type is common (3-5)
  frequency_pct: number;           // Percentage of total grievances (0-100)
  typical_distress: "CRITICAL" | "HIGH" | "MEDIUM" | "NORMAL";
  examples: string[];              // Example grievances (2-4)
}

interface StatusCategory {
  status: string;                  // Status name in English
  telugu: string;                  // Telugu translation
  description: string;             // What this status means
}

interface GrievanceTypeFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_distress_levels: 4;
    total_common_types: number;
    schema: "GrievanceTypeSchema";
  };
  distress_levels: DistressLevel[];      // Always 4 levels
  common_grievance_types: GrievanceType[];
  status_categories: StatusCategory[];
  usage_notes: {
    sentiment_detection: string;
    routing: string;
    sla: string;
    keywords: string;
    frequency: string;
  };
}
```

**Validation Rules:**
- `distress_levels`: Must have exactly 4 levels (CRITICAL, HIGH, MEDIUM, NORMAL)
- `value`: Must match level (CRITICAL=4, HIGH=3, MEDIUM=2, NORMAL=1)
- `sla_hours`: Must be [24, 72, 168, 336] respectively
- `frequency_pct` across all types: Should sum to ~100%
- `keywords_english.length ≈ keywords_telugu.length`

---

### LapseDefinitionSchema
**File:** `tier1_core/lapse_definitions.json`
**Usage:** Audit classification, lapse prediction, quality control

```typescript
interface Lapse {
  id: number;                      // Unique ID (1-13)
  name: string;                    // Lapse name in English
  telugu: string;                  // Telugu name
  type: "behavioral" | "procedural";
  severity: "critical" | "high" | "medium";
  description: string;             // Detailed explanation
  frequency_pct: number;           // Percentage in Guntur audit data (0-100)
  rank: number;                    // Rank by frequency (1=most common)
  examples: string[];              // Real examples from audits (2-4)
  detection_keywords: string[];    // Keywords for automated detection (5-10)
}

interface LapseSummary {
  total_lapses: number;
  behavioral_count: number;
  procedural_count: number;
  behavioral_frequency_pct: number;
  procedural_frequency_pct: number;
  top_3_lapses: string[];          // Descriptions with percentages
  critical_severity_count: number;
  high_severity_count: number;
  medium_severity_count: number;
}

interface LapseDefinitionFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_lapses: 13;
    behavioral_lapses: 5;
    procedural_lapses: 8;
    schema: "LapseDefinitionSchema";
  };
  lapses: Lapse[];
  summary: LapseSummary;
  usage_notes: {
    classification: string;
    detection: string;
    severity: string;
    training: string;
    bilingual: string;
  };
}
```

**Validation Rules:**
- `id`: Must be unique, 1-13
- `type`: Must be "behavioral" or "procedural"
- `severity`: Must be "critical", "high", or "medium"
- `frequency_pct`: 0.0-100.0
- `rank`: Must be unique, 1-13
- Behavioral lapses: IDs 4, 10, 11, 12, 13
- Procedural lapses: IDs 1, 2, 3, 5, 6, 7, 8, 9

---

### ResponseTemplateSchema
**File:** `tier1_core/response_templates.json`
**Usage:** Automated response generation, template selection

```typescript
interface TemplateCategory {
  category: string;                // Category name
  count: number;                   // Number of templates in this category
  statuses?: string[];             // Applicable statuses
  subcases?: string[];             // Applicable subcases
  description: string;             // Category description
}

interface SampleTemplate {
  status: string;                  // Primary status
  telugu: string;                  // Telugu template text (may contain [VARIABLE])
  english: string;                 // English translation
  variables: string[];             // List of required variables to replace
  use_case: string;                // When to use this template
}

interface StandardFooter {
  telugu: string;                  // Standard Telugu footer text
  english: string;                 // English translation
}

interface ResponseTemplateFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_templates: 54;
    language: "te";
    schema: "ResponseTemplateSchema";
    full_data_location: string;    // Path to complete template file
  };
  template_categories: TemplateCategory[];
  sample_templates: SampleTemplate[];
  standard_footer: StandardFooter;
  usage_notes: {
    template_selection: string;
    variable_substitution: string;
    bilingual: string;
    contact_info: string;
    full_dataset: string;
  };
}
```

**Full Template Schema** (in `backend/ml/data/extracted_docs/official_telugu_templates.json`):
```typescript
interface FullTemplate {
  status: string;                  // Primary status
  subcase: string;                 // Subcase/scenario (may be empty)
  template_text: string;           // Full Telugu template with [VARIABLE]
  sample_text: string | null;      // Example with variables filled in
  language: "te";
  type: "official_response";
}

interface FullTemplateFile {
  source: string;
  extracted_at: string;            // ISO datetime
  count: 54;
  templates: FullTemplate[];
}
```

**Validation Rules:**
- `total_templates`: Must equal sum of category counts
- `variables`: Must match [VARIABLE] occurrences in template_text
- All Telugu text must be UTF-8 encoded
- `sample_text`: If present, must not contain [VARIABLE]

---

## Tier 2 Training Schemas

### ClassificationTrainingSchema
**File:** `tier2_training/classification/muril_classification_training.json`
**Usage:** Training department classification models

```typescript
interface ClassificationSample {
  text: string;                    // Telugu grievance text (10-500 words)
  department: string;              // Department name in English
  department_code: string;         // Department code (e.g., "REV", "MAUD")
  _source?: string;                // Optional: Source dataset identifier
}

interface ClassificationTrainingFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_samples: 14876;
    total_labels: 15;                // Number of unique departments
    language: "te";
    schema: "ClassificationTrainingSchema";
  };
  samples: ClassificationSample[];
  label_distribution: {
    [department: string]: number;   // Count per department
  };
  usage_notes: {
    model_type: string;             // e.g., "MuRIL", "Telugu-BERT"
    task: string;                   // "Multi-class classification"
    imbalance: string;              // Notes on class imbalance
  };
}
```

**Validation Rules:**
- `text`: Non-empty, primarily Telugu script
- `department`: Must match one of 30 department names
- `department_code`: Must match department code
- Total samples: 14,876 (fixed)
- Labels: 15 unique departments (some grouped)

---

### SentimentTrainingSchema
**File:** `tier2_training/sentiment/muril_sentiment_training.json`
**Usage:** Training distress level detection models

```typescript
interface SentimentSample {
  text: string;                    // Telugu grievance text
  sentiment: "CRITICAL" | "HIGH" | "MEDIUM" | "NORMAL";
  distress_level: 1 | 2 | 3 | 4;  // Numeric encoding
  _source?: string;
}

interface SentimentTrainingFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_samples: 14876;
    total_labels: 4;
    language: "te";
    distribution: "balanced";       // Important: classes are balanced
    schema: "SentimentTrainingSchema";
  };
  samples: SentimentSample[];
  label_distribution: {
    CRITICAL: number;               // ~3,722
    HIGH: number;                   // ~3,722
    MEDIUM: number;                 // ~3,716
    NORMAL: number;                 // ~3,716
  };
  usage_notes: {
    model_type: string;
    task: string;                   // "Multi-class classification"
    balance: string;                // "Classes are balanced"
  };
}
```

**Validation Rules:**
- `text`: Non-empty, primarily Telugu
- `sentiment`: Must be one of 4 levels
- `distress_level`: Must match sentiment (CRITICAL=4, HIGH=3, MEDIUM=2, NORMAL=1)
- Distribution: Should be roughly balanced (~3,700 per class)

---

### LapseTrainingSchema
**File:** `tier2_training/lapse_prediction/guntur_audit_training.json`
**Usage:** Training lapse prediction models for audit quality

```typescript
interface LapseSample {
  grievance_id: string;            // Unique grievance identifier
  grievance_text: string;          // Original grievance text (if available)
  officer_endorsement: string;     // Officer's closure comment
  department: string;              // Department name
  lapse_categories: number[];      // Array of lapse IDs (multi-label!)
  improper: boolean;               // Whether case had improper redressal
  _source?: string;
}

interface LapseTrainingFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_samples: 2298;
    total_labels: 13;
    type: "multi-label";            // Important: multi-label classification
    district: "Guntur";
    audit_date: "2025-11-07";
    schema: "LapseTrainingSchema";
  };
  samples: LapseSample[];
  label_distribution: {
    [lapse_id: number]: number;     // Count per lapse type
  };
  label_frequency: {
    [lapse_id: number]: number;     // Percentage per lapse type
  };
  usage_notes: {
    model_type: string;
    task: string;                   // "Multi-label classification"
    imbalance: string;              // "Highly imbalanced (42% vs 0.4%)"
    strategy: string;               // Recommended handling strategy
  };
}
```

**Validation Rules:**
- `lapse_categories`: Array of integers 1-13
- `lapse_categories`: Can be empty (no lapse) or have multiple values
- `improper`: true if lapse_categories.length > 0
- Distribution: Highly imbalanced (top: 42.19%, bottom: 0.44%)
- Source: Single district (Guntur) - not representative of full state

---

## Tier 3 Reference Schemas

### OfficerHierarchySchema
**File:** `tier3_reference/officer_hierarchy.json`

```typescript
interface Officer {
  designation: string;             // Official designation (e.g., "Collector", "MPDO")
  department: string;              // Parent department
  subdepartment?: string;          // Subdepartment if applicable
  level: number;                   // Hierarchy level (1=highest)
  reports_to?: string;             // Superior officer designation
  handles_grievances: string[];    // Types of grievances this officer handles
  typical_sla_hours: number;       // Typical response time
}

interface OfficerHierarchyFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_officers: number;         // 106+ HODs
    total_departments: 30;
    schema: "OfficerHierarchySchema";
  };
  officers: Officer[];
  hierarchy_levels: {
    [level: number]: string[];      // Designations at each level
  };
}
```

---

### DistrictDataSchema
**File:** `tier3_reference/district_data.json`

```typescript
interface District {
  district_name: string;           // Official district name
  district_code: string;           // 2-3 letter code
  mandals: string[];               // List of mandal names (10-70 per district)
  constituencies: string[];        // MLA constituencies (2-10 per district)
  total_grievances: number;        // Total grievances received
  satisfaction_score: number;      // Avg satisfaction (0-5 scale)
  improper_percentage: number;     // Audit improper redressal rate (0-100)
  population: number;              // District population (optional)
}

interface DistrictDataFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_districts: 26;
    schema: "DistrictDataSchema";
  };
  districts: District[];
}
```

---

### ServiceCatalogSchema
**File:** `tier3_reference/service_catalog.json`

```typescript
interface Service {
  service_id: string;              // Unique service ID
  service_name_english: string;
  service_name_telugu: string;
  department: string;              // Parent department
  subdepartment?: string;
  category: string;                // Service category
  typical_sla_days: number;        // Standard processing time
  documents_required: string[];    // Required documents
  fee?: number;                    // Service fee if applicable
}

interface ServiceCatalogFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_services: number;         // 200+
    schema: "ServiceCatalogSchema";
  };
  services: Service[];
  by_department: {
    [department: string]: Service[];
  };
}
```

---

### SLARulesSchema
**File:** `tier3_reference/sla_rules.json`

```typescript
interface SLARule {
  rule_id: string;                 // Unique rule ID
  grievance_type?: string;         // Specific grievance type
  distress_level?: "CRITICAL" | "HIGH" | "MEDIUM" | "NORMAL";
  department?: string;             // Specific department
  sla_hours: number;               // Response deadline in hours
  escalation_hours: number;        // When to escalate
  escalation_to: string;           // Designation to escalate to
  priority_multiplier: number;     // Adjustment factor (0.5-2.0)
}

interface SLARulesFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    schema: "SLARulesSchema";
  };
  default_slas: {
    CRITICAL: 24;
    HIGH: 72;
    MEDIUM: 168;
    NORMAL: 336;
  };
  rules: SLARule[];
  escalation_chain: {
    [level: number]: string[];      // Escalation hierarchy
  };
}
```

---

## Tier 4 Audit Schemas

### AuditReportSchema
**File:** `tier4_audit/guntur_audit.json`

```typescript
interface AuditCase {
  case_id: string;                 // Unique case identifier
  district: "Guntur";
  mandal?: string;
  department: string;
  officer: string;                 // Responsible officer
  grievance_text?: string;
  officer_endorsement?: string;
  improper: boolean;
  lapse_categories: number[];      // Lapse IDs from lapse_definitions.json
  audit_date: string;              // ISO date
  citizen_feedback?: string;
}

interface DepartmentBreakdown {
  total_redressed: number;
  audited: number;
  improper_percentage: number;
  common_lapses: string[];         // Top 3 lapse names
}

interface AuditReportFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    schema: "AuditReportSchema";
  };
  audit_metadata: {
    district: "Guntur";
    audit_date: "2025-11-07";
    total_cases_audited: 2298;
    total_cases_redressed: 17206;
    improper_redressal_percentage: 22.80;
  };
  cases: AuditCase[];
  department_breakdown: {
    [department: string]: DepartmentBreakdown;
  };
  lapse_summary: {
    [lapse_id: number]: {
      count: number;
      percentage: number;
      examples: string[];
    };
  };
}
```

---

### PreAuditSchema
**File:** `tier4_audit/constituency_preaudit.json`

```typescript
interface ConstituencyPreAudit {
  district: string;
  constituency: string;
  mandal?: string;
  total_cases: number;
  improper_percentage: number;
  period: string;                  // e.g., "April-October 2025"
  top_lapses: string[];            // Top 3-5 lapse categories
}

interface PreAuditFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_cases: 243133;
    districts_covered: 26;
    period: "April-October 2025";
    schema: "PreAuditSchema";
  };
  constituencies: ConstituencyPreAudit[];
  district_summary: {
    [district: string]: {
      total_audited: number;
      improper_percentage: number;
      top_constituency: string;
    };
  };
}
```

---

### CallCenterFeedbackSchema
**File:** `tier4_audit/call_center_feedback.json`

```typescript
interface DepartmentFeedback {
  sno: number;
  department: string;
  total_feedback: number;
  avg_satisfaction_5: number;      // Average on 0-5 scale
  pct_satisfied: number;           // Percentage satisfied (0-100)
  computed_metrics: {
    dept_risk_score: number;       // (5 - avg) / 4
    rank: number;                  // Rank by volume
    relative_weight: number;       // Normalized weight for training
  };
}

interface CallCenterFeedbackFile {
  _metadata: {
    created: string;
    version: string;
    description: string;
    _source: string[];
    total_records: 93892;
    total_departments: 31;
    schema: "CallCenterFeedbackSchema";
  };
  departments: DepartmentFeedback[];
  summary: {
    total_records: number;
    avg_satisfaction: number;
    overall_satisfied_pct: number;
    satisfaction_distribution: {
      very_dissatisfied_0_marks: number;
      dissatisfied_0_marks: number;
      neutral_0_marks: number;
      satisfied_2_5_marks: number;
      very_satisfied_5_marks: number;
    };
  };
}
```

---

## Common Field Types

### Metadata Structure
All files include a `_metadata` object:

```typescript
interface Metadata {
  created: string;                 // ISO date "YYYY-MM-DD"
  version: string;                 // Semantic version "X.Y"
  description: string;             // Human-readable description
  _source: string[];               // Array of source file paths
  schema: string;                  // Schema name (e.g., "DepartmentSchema")
  // ... other schema-specific fields
}
```

### Language Fields
For bilingual data:

```typescript
interface BilingualField {
  field_english: string;           // English version
  field_telugu: string;            // Telugu version (UTF-8)
}
```

### Date/Time Fields
```typescript
type ISODate = string;             // Format: "YYYY-MM-DD"
type ISODateTime = string;         // Format: "YYYY-MM-DDTHH:mm:ss.ffffff"
```

---

## Validation Rules

### General Rules
1. All JSON must be valid JSON (no trailing commas, proper escaping)
2. All Telugu text must be UTF-8 encoded (Unicode range U+0C00 to U+0C7F)
3. All files must have `_metadata` object
4. All percentages must be 0.0-100.0
5. All dates must be ISO format "YYYY-MM-DD"

### Schema-Specific Rules
1. **DepartmentSchema:** Total keywords must match sum of English + Telugu keywords
2. **GrievanceTypeSchema:** Must have exactly 4 distress levels
3. **LapseDefinitionSchema:** Must have exactly 13 lapses (5 behavioral, 8 procedural)
4. **ClassificationTrainingSchema:** Total samples must be 14,876
5. **SentimentTrainingSchema:** Classes should be balanced (~3,700 each)
6. **LapseTrainingSchema:** Multi-label (array of lapse IDs)

### Data Integrity
1. Foreign keys must reference valid IDs (e.g., lapse_id must be 1-13)
2. Department codes must match across all files
3. District names must be consistent across files
4. Officer designations must match hierarchy definitions

---

## Version History

**v1.0 (2025-11-25):** Initial schema documentation
- Documented all Tier 1, 2, 3, 4 schemas
- Established validation rules
- Created TypeScript interface definitions

---

## Notes

- All schemas use TypeScript interfaces for clarity
- In Python, use `typing` module for equivalent type hints
- For JSON Schema validation, convert TypeScript interfaces to JSON Schema
- Unicode handling: Always use `encoding='utf-8'` when reading/writing files
- Multi-label classification: Use arrays for `lapse_categories` field
- Imbalanced data: Use weighted losses or sampling strategies for lapses

---

**Schema Owner:** DHRUVA Backend ML Team
**Last Updated:** 2025-11-25
**For Questions:** See `_INDEX.json` or `_QUICK_REFERENCE.md`
