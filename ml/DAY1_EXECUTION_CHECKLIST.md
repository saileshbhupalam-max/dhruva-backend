# DAY 1: ML TRAINING & DATABASE IMPORT - EXECUTION CHECKLIST

**Date**: 2025-11-25
**Estimated Duration**: 6-8 hours
**Current Status**: Starting Phase 1

---

## 📋 MASTER CHECKLIST

### Phase 1: Environment Setup (30 minutes)
- [ ] 1.1 Install XGBoost
  - [ ] 1.1.1 Run pip install xgboost
  - [ ] 1.1.2 Verify import works
  - [ ] 1.1.3 Check version compatibility
- [ ] 1.2 Install optional dependencies
  - [ ] 1.2.1 Install lightgbm (backup)
  - [ ] 1.2.2 Install joblib (model serialization)
  - [ ] 1.2.3 Install plotly (visualization)
- [ ] 1.3 Create .env file
  - [ ] 1.3.1 Copy .env.example to .env
  - [ ] 1.3.2 Update DATABASE_URL
  - [ ] 1.3.3 Update JWT_SECRET_KEY
  - [ ] 1.3.4 Verify .env loads correctly

### Phase 2: Database Schema (2 hours)
- [ ] 2.1 Create AudioClip model
  - [ ] 2.1.1 Create backend/app/models/audio_clip.py
  - [ ] 2.1.2 Define table schema (id, filename, duration, transcription, etc.)
  - [ ] 2.1.3 Add relationships if needed
  - [ ] 2.1.4 Update models/__init__.py
- [ ] 2.2 Create DepartmentKeyword model
  - [ ] 2.2.1 Create backend/app/models/department_keyword.py
  - [ ] 2.2.2 Define table schema (id, department_id, keyword_english, keyword_telugu, etc.)
  - [ ] 2.2.3 Add foreign key to departments
  - [ ] 2.2.4 Update models/__init__.py
- [ ] 2.3 Create Officer model
  - [ ] 2.3.1 Create backend/app/models/officer.py
  - [ ] 2.3.2 Define table schema (id, department_id, designation, performance metrics, etc.)
  - [ ] 2.3.3 Add computed fields for metrics
  - [ ] 2.3.4 Update models/__init__.py
- [ ] 2.4 Create SatisfactionMetric model
  - [ ] 2.4.1 Create backend/app/models/satisfaction_metric.py
  - [ ] 2.4.2 Define table schema (id, department_id, total_feedback, avg_satisfaction, etc.)
  - [ ] 2.4.3 Add risk score computation
  - [ ] 2.4.4 Update models/__init__.py
- [ ] 2.5 Create MessageTemplate model
  - [ ] 2.5.1 Create backend/app/models/message_template.py
  - [ ] 2.5.2 Define table schema (id, category, text_telugu, text_english, etc.)
  - [ ] 2.5.3 Add template variable tracking
  - [ ] 2.5.4 Update models/__init__.py
- [ ] 2.6 Create LapseCase model
  - [ ] 2.6.1 Create backend/app/models/lapse_case.py
  - [ ] 2.6.2 Define table schema (id, district, department, lapse_category, etc.)
  - [ ] 2.6.3 Add foreign keys and indexes
  - [ ] 2.6.4 Update models/__init__.py
- [ ] 2.7 Generate migration
  - [ ] 2.7.1 Run alembic revision --autogenerate -m "add_ml_training_tables"
  - [ ] 2.7.2 Review generated migration file
  - [ ] 2.7.3 Add manual indexes if needed
  - [ ] 2.7.4 Test migration syntax
- [ ] 2.8 Apply migration
  - [ ] 2.8.1 Run alembic upgrade head
  - [ ] 2.8.2 Verify all 6 tables created
  - [ ] 2.8.3 Check indexes created correctly
  - [ ] 2.8.4 Test database connection

### Phase 3: Data Import (2 hours)
- [ ] 3.1 Create import script for Audio Transcriptions
  - [ ] 3.1.1 Create backend/ml/scripts/import_audio.py
  - [ ] 3.1.2 Load audio_transcriptions.json
  - [ ] 3.1.3 Parse and insert 46 records
  - [ ] 3.1.4 Validate import (count = 46)
- [ ] 3.2 Create import script for PGRS Keywords
  - [ ] 3.2.1 Create backend/ml/scripts/import_keywords.py
  - [ ] 3.2.2 Load pgrs_book_keywords.json
  - [ ] 3.2.3 Parse and insert 709 keywords across 30 departments
  - [ ] 3.2.4 Validate import (count = 709)
- [ ] 3.3 Create import script for Officer Performance
  - [ ] 3.3.1 Create backend/ml/scripts/import_officers.py
  - [ ] 3.3.2 Load officer_performance.json
  - [ ] 3.3.3 Parse and insert 490 officer records
  - [ ] 3.3.4 Validate import (count = 490)
- [ ] 3.4 Create import script for Call Center Satisfaction
  - [ ] 3.4.1 Create backend/ml/scripts/import_satisfaction.py
  - [ ] 3.4.2 Load call_center_satisfaction.json
  - [ ] 3.4.3 Parse and insert 31 department records
  - [ ] 3.4.4 Validate import (count = 31)
- [ ] 3.5 Create import script for Message Templates
  - [ ] 3.5.1 Create backend/ml/scripts/import_templates.py
  - [ ] 3.5.2 Load message_templates.json
  - [ ] 3.5.3 Parse and insert 54 template records
  - [ ] 3.5.4 Validate import (count = 54)
- [ ] 3.6 Create import script for Audit Reports
  - [ ] 3.6.1 Create backend/ml/scripts/import_lapses.py
  - [ ] 3.6.2 Load audit_reports.json
  - [ ] 3.6.3 Parse and insert 2,298 Guntur cases
  - [ ] 3.6.4 Validate import (count = 2,298)
- [ ] 3.7 Run master import script
  - [ ] 3.7.1 Create backend/ml/scripts/import_all.py
  - [ ] 3.7.2 Run all imports in sequence
  - [ ] 3.7.3 Verify total record counts
  - [ ] 3.7.4 Generate import report

### Phase 4: ML Model Training - Lapse Prediction (2 hours)
- [ ] 4.1 Prepare training data
  - [ ] 4.1.1 Create backend/ml/train_lapse_predictor.py
  - [ ] 4.1.2 Load 2,298 lapse cases from database
  - [ ] 4.1.3 Extract features (dept, officer, workload, satisfaction)
  - [ ] 4.1.4 Encode categorical variables
  - [ ] 4.1.5 Split train/test (80/20)
- [ ] 4.2 Train XGBoost model
  - [ ] 4.2.1 Configure hyperparameters
  - [ ] 4.2.2 Train on 1,838 cases
  - [ ] 4.2.3 Validate on 460 cases
  - [ ] 4.2.4 Calculate ROC-AUC score
- [ ] 4.3 Evaluate model performance
  - [ ] 4.3.1 Generate confusion matrix
  - [ ] 4.3.2 Calculate precision/recall/F1
  - [ ] 4.3.3 Analyze feature importance
  - [ ] 4.3.4 Test on edge cases
- [ ] 4.4 Save model artifacts
  - [ ] 4.4.1 Save model to backend/ml/models/lapse_predictor_v1.pkl
  - [ ] 4.4.2 Save feature encoder
  - [ ] 4.4.3 Save model metadata (version, metrics, etc.)
  - [ ] 4.4.4 Generate model card documentation

### Phase 5: ML Model Training - Telugu Classifier (1 hour)
- [ ] 5.1 Prepare training data
  - [ ] 5.1.1 Create backend/ml/train_telugu_classifier.py
  - [ ] 5.1.2 Load 709 keywords from database
  - [ ] 5.1.3 Load 54 templates from database
  - [ ] 5.1.4 Create synthetic training examples
  - [ ] 5.1.5 Split train/test (80/20)
- [ ] 5.2 Train TF-IDF + Logistic Regression
  - [ ] 5.2.1 Configure TF-IDF vectorizer (Telugu + English)
  - [ ] 5.2.2 Train logistic regression classifier
  - [ ] 5.2.3 Validate on test set
  - [ ] 5.2.4 Calculate accuracy metrics
- [ ] 5.3 Evaluate classifier performance
  - [ ] 5.3.1 Test on real Telugu grievances (if available)
  - [ ] 5.3.2 Calculate per-department accuracy
  - [ ] 5.3.3 Compare with keyword-based baseline
  - [ ] 5.3.4 Analyze misclassifications
- [ ] 5.4 Save classifier artifacts
  - [ ] 5.4.1 Save model to backend/ml/models/telugu_classifier_v1.pkl
  - [ ] 5.4.2 Save TF-IDF vectorizer
  - [ ] 5.4.3 Save department mappings
  - [ ] 5.4.4 Generate classifier documentation

### Phase 6: Validation & Documentation (1 hour)
- [ ] 6.1 Create validation report
  - [ ] 6.1.1 Create backend/ml/DAY1_TRAINING_REPORT.md
  - [ ] 6.1.2 Document lapse predictor metrics
  - [ ] 6.1.3 Document Telugu classifier metrics
  - [ ] 6.1.4 Include visualizations (confusion matrices, etc.)
- [ ] 6.2 Test models via API
  - [ ] 6.2.1 Create test endpoint for lapse prediction
  - [ ] 6.2.2 Create test endpoint for department classification
  - [ ] 6.2.3 Test with sample inputs
  - [ ] 6.2.4 Verify response formats
- [ ] 6.3 Generate model cards
  - [ ] 6.3.1 Create lapse_predictor_v1_card.md
  - [ ] 6.3.2 Create telugu_classifier_v1_card.md
  - [ ] 6.3.3 Document use cases and limitations
  - [ ] 6.3.4 Include example predictions
- [ ] 6.4 Update requirements.txt
  - [ ] 6.4.1 Add xgboost to requirements.txt
  - [ ] 6.4.2 Add any new dependencies
  - [ ] 6.4.3 Pin versions
  - [ ] 6.4.4 Test pip install -r requirements.txt

### Phase 7: Git Commit (15 minutes)
- [ ] 7.1 Stage all changes
  - [ ] 7.1.1 Stage 6 new model files
  - [ ] 7.1.2 Stage migration 003
  - [ ] 7.1.3 Stage import scripts
  - [ ] 7.1.4 Stage training scripts
  - [ ] 7.1.5 Stage trained models (.pkl files)
  - [ ] 7.1.6 Stage documentation
- [ ] 7.2 Create comprehensive commit
  - [ ] 7.2.1 Write detailed commit message
  - [ ] 7.2.2 Include metrics and stats
  - [ ] 7.2.3 Reference Day 0 extraction
  - [ ] 7.2.4 Note production readiness
- [ ] 7.3 Push to remote
  - [ ] 7.3.1 Run git push origin main
  - [ ] 7.3.2 Verify commit on GitHub
  - [ ] 7.3.3 Check CI/CD status (if enabled)
  - [ ] 7.3.4 Tag release if needed

---

## 🎯 SUCCESS CRITERIA

### Database Import
- ✅ All 6 tables created successfully
- ✅ Total records imported: 3,638 (46+709+490+31+54+2,298)
- ✅ No import errors or data loss
- ✅ Foreign keys working correctly

### Lapse Prediction Model
- ✅ ROC-AUC score ≥0.75 (target: 0.75-0.80)
- ✅ Precision ≥0.70 on top lapse category
- ✅ Model saved and loadable
- ✅ Prediction time <100ms

### Telugu Classifier
- ✅ Accuracy ≥0.85 (target: 85%+)
- ✅ All 30 departments covered
- ✅ Telugu text handling correct
- ✅ Model saved and loadable

### Documentation
- ✅ Training report generated
- ✅ Model cards created
- ✅ Import validation logs available
- ✅ All code committed to git

---

## ⏱️ TIME TRACKING

| Phase | Estimated | Actual | Status |
|-------|-----------|--------|--------|
| Phase 1: Setup | 30 min | - | Pending |
| Phase 2: Database | 2 hours | - | Pending |
| Phase 3: Import | 2 hours | - | Pending |
| Phase 4: Lapse Model | 2 hours | - | Pending |
| Phase 5: Telugu Model | 1 hour | - | Pending |
| Phase 6: Validation | 1 hour | - | Pending |
| Phase 7: Git | 15 min | - | Pending |
| **TOTAL** | **8h 45min** | **-** | **Not Started** |

---

## 🚨 BLOCKERS & ISSUES

| Issue | Impact | Resolution | Status |
|-------|--------|------------|--------|
| - | - | - | - |

---

## 📝 NOTES & DECISIONS

- Using XGBoost for lapse prediction (vs LightGBM) - industry standard
- Using TF-IDF + LogReg for Telugu (vs deep learning) - faster, simpler
- Storing models as .pkl files (vs ONNX) - easier Python integration
- Training on CPU only (vs GPU) - sufficient for dataset size

---

**Status**: ⏳ READY TO START
**Next Step**: Phase 1.1 - Install XGBoost
**Estimated Completion**: ~8 hours from start
