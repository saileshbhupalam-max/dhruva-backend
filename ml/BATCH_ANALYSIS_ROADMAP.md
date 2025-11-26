# DHRUVA Batch Analysis System - Roadmap

**Status**: PLANNED (Post-Integration)
**Impact**: 100x value for government with 1 lakh+ cases

---

## The Pitch

> "Give us your 1 lakh unaudited cases. In **24 hours**, we'll give you:
>
> 1. **Top 5,000 cases** most likely improperly redressed (audit priority list)
> 2. **15 officers and 8 areas** that need immediate intervention
> 3. **4,000 cases auto-resolved** or correctly re-routed
>
> All verifiable against your manual audit results."

---

## Three High-Impact Systems to Build

### 1. Instant Audit Engine
**Process 1 lakh cases in minutes, flag ~22% improper redressals**

```
Input: 100,000 historical cases (CSV/JSON)
Processing: ~5 minutes
Output:
  - Top 5,000 high-confidence improper cases (prioritized audit list)
  - Lapse type breakdown (behavioral vs procedural)
  - Officer-wise improper rate ranking
  - Department-wise quality scores
```

**Value**: 10x audit efficiency. Months of manual work → minutes.

### 2. Pattern Intelligence Dashboard
**Surface systemic failures and policy insights**

```
Analytics to generate:
  - Officer Patterns: "Officer X has 45% reopen rate vs 12% average"
  - Area Hotspots: "Ward 7 Guntur has 5x water complaints"
  - Department Bottlenecks: "Revenue takes 45 days avg vs 15 day SLA"
  - Seasonal Trends: "Pension complaints spike 3x in January"
  - Shallow Fix Detection: Cases reopened within 30 days
```

**Value**: Policy-level insights that prevent future grievances.

### 3. Auto-Triage Backlog Clearer
**Clear 40% of backlog without human touch**

```
Input: 10,000 pending/unassigned cases
Output:
  - 4,000 auto-resolved (routine, duplicate, already addressed)
  - 2,000 auto-routed to correct department
  - 1,000 flagged CRITICAL (immediate attention)
  - 3,000 complex cases for human review
```

**Value**: Clear backlog in hours, not months.

---

## Technical Implementation Plan

### Phase 1: Batch Processing Engine
```python
# batch_analyzer.py
class BatchAnalyzer:
    def __init__(self):
        self.processor = GrievanceProcessor()

    def analyze_bulk(self, cases: List[Dict], batch_size=1000):
        """Process cases in batches with progress tracking"""
        pass

    def generate_audit_report(self, results) -> AuditReport:
        """Generate prioritized audit list"""
        pass

    def generate_pattern_report(self, results) -> PatternReport:
        """Surface systemic patterns"""
        pass

    def generate_triage_report(self, results) -> TriageReport:
        """Auto-triage recommendations"""
        pass
```

### Phase 2: Report Generators
- PDF/Excel export for government officials
- Executive summary (1-page)
- Detailed findings with evidence
- Action items with priority ranking

### Phase 3: API Endpoints
```
POST /ml/batch/upload - Upload CSV/JSON of cases
GET /ml/batch/{job_id}/status - Check processing status
GET /ml/batch/{job_id}/audit-report - Download audit report
GET /ml/batch/{job_id}/pattern-report - Download pattern analysis
GET /ml/batch/{job_id}/triage-report - Download triage recommendations
```

### Phase 4: Dashboard Integration
- Real-time processing progress
- Interactive visualizations
- Drill-down capability
- Export to multiple formats

---

## Data Requirements

### Input Format (CSV/JSON)
```json
{
  "grievance_id": "PGRS-2025-GTR-12345",
  "grievance_text": "Telugu/English text...",
  "department": "Revenue",
  "officer_id": "OFF123",
  "officer_name": "Name",
  "district": "Guntur",
  "mandal": "Tenali",
  "status": "Closed",
  "resolution_text": "Action taken...",
  "submitted_date": "2025-01-15",
  "resolved_date": "2025-01-20",
  "citizen_feedback": "Satisfied/Unsatisfied"
}
```

### Output Reports
1. **audit_priority_list.xlsx** - Cases ranked by improper likelihood
2. **officer_performance.xlsx** - Officer-wise metrics
3. **area_hotspots.xlsx** - Geographic patterns
4. **department_analytics.xlsx** - Department-wise analysis
5. **executive_summary.pdf** - 1-page overview for leadership

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Processing Speed | 1 lakh cases < 10 minutes |
| Audit Precision | >70% of flagged cases are truly improper |
| Pattern Detection | Surface top 10 systemic issues |
| Auto-Triage Rate | 40% cases handled without human |
| Report Generation | < 2 minutes after processing |

---

## Implementation Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | 2 days | Batch processing engine |
| Phase 2 | 1 day | Report generators |
| Phase 3 | 1 day | API endpoints |
| Phase 4 | 2 days | Dashboard integration |
| Testing | 1 day | End-to-end validation |

**Total: ~1 week post-integration**

---

## Demo Strategy

1. Get sample 10,000 cases from government (anonymized if needed)
2. Run batch analysis live in front of officials
3. Show audit priority list - verify against their known problematic cases
4. Surface patterns they weren't aware of
5. Demonstrate auto-triage clearing backlog

**This proves immediate, verifiable value.**

---

*Document created: 2025-11-25*
*Status: Ready to build after core integration complete*
