"""
Smart Clarifying Questions Generator
=====================================
Uses knowledge base + keyword extraction to generate context-aware questions.
No external LLM API required - works offline.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Load knowledge base
BASE_DIR = Path(__file__).parent
KB_DIR = BASE_DIR / "data" / "knowledge_base" / "tier1_core"


class ClarifyingQuestionsGenerator:
    """Generates smart clarifying questions based on grievance content and AI predictions."""

    def __init__(self):
        self.departments = {}
        self.grievance_types = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load departments and grievance types from knowledge base."""
        try:
            with open(KB_DIR / "departments.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for dept in data.get("departments", []):
                    name = dept.get("name_english", "")
                    # Map to our simplified department names
                    simplified = self._simplify_dept_name(name)
                    if simplified:
                        self.departments[simplified] = {
                            "keywords_en": dept.get("keywords_english", []),
                            "keywords_te": dept.get("keywords_telugu", []),
                            "common_subjects": dept.get("common_subjects", []),
                            "subdepartments": dept.get("subdepartments", []),
                        }

            with open(KB_DIR / "grievance_types.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.grievance_types = data.get("common_grievance_types", [])

        except Exception as e:
            print(f"Warning: Could not load knowledge base: {e}")

    def _simplify_dept_name(self, full_name: str) -> Optional[str]:
        """Map full department names to simplified versions used in our model."""
        mapping = {
            "Agriculture And Co-operation": "Agriculture",
            "Animal Husbandry, Dairy Development And Fisheries": "Animal Husbandry",
            "Consumer Affairs, Food And Civil Supplies": "Civil Supplies",
            "Energy": "Energy",
            "Finance": "Finance",
            "Health, Medical And Family Welfare": "Health",
            "Home (Police)": "Police",
            "Housing": "Housing",
            "Municipal Administration And Urban Development": "Municipal Administration",
            "Panchayat Raj And Rural Development": "Panchayat Raj",
            "Revenue": "Revenue",
            "Roads And Buildings": "Transport",
            "School Education": "Education",
            "Social Welfare": "Social Welfare",
            "Transport": "Transport",
            "Water Resources": "Water Resources",
            "Women, Children, Differently Abled And Senior Citizens": "Women & Child Welfare",
        }
        return mapping.get(full_name)

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract meaningful keywords from grievance text."""
        # Lowercase and tokenize
        text_lower = text.lower()
        words = re.findall(r'\b[a-z]+\b', text_lower)

        # Common grievance-related words to look for
        important_keywords = [
            # Payment related
            "pension", "payment", "money", "salary", "wages", "arrears", "dues",
            # Documents
            "certificate", "card", "document", "license", "permit", "patta",
            # Infrastructure
            "road", "water", "electricity", "drainage", "building", "school",
            # Services
            "hospital", "police", "ration", "shop", "office",
            # Issues
            "delay", "corruption", "bribe", "harassment", "theft", "damage",
            # People
            "teacher", "officer", "doctor", "dealer",
            # Specific
            "land", "house", "crop", "loan", "subsidy", "scheme",
        ]

        found = [w for w in words if w in important_keywords]
        return list(set(found))

    def _detect_telugu(self, text: str) -> bool:
        """Check if text contains Telugu characters."""
        telugu_range = re.compile(r'[\u0C00-\u0C7F]')
        return bool(telugu_range.search(text))

    def generate_questions(
        self,
        grievance_text: str,
        predicted_dept: str,
        top_3_depts: List[Dict],
        confidence: float
    ) -> List[Dict]:
        """
        Generate smart clarifying questions based on context.

        Returns list of questions with format:
        [
            {
                "question": "Is this about pension payment?",
                "question_telugu": "ఇది పెన్షన్ చెల్లింపు గురించి ఆ?",
                "target_dept": "Social Welfare",
                "confidence_boost": 0.15,
                "relevance_score": 0.9
            }
        ]
        """
        questions = []
        is_telugu = self._detect_telugu(grievance_text)
        extracted_keywords = self._extract_keywords_from_text(grievance_text)

        # Get top 2-3 departments to generate questions for
        candidate_depts = [d["department"] for d in top_3_depts[:3]]

        for dept in candidate_depts:
            dept_info = self.departments.get(dept, {})
            dept_keywords = dept_info.get("keywords_en", [])
            common_subjects = dept_info.get("common_subjects", [])

            # Find which keywords from grievance match this department
            matching_keywords = [k for k in extracted_keywords if k in dept_keywords]

            # Generate questions based on common subjects NOT mentioned
            for subject in common_subjects[:3]:
                # Check if this subject is already clearly mentioned
                subject_words = subject.lower().split()
                already_mentioned = any(w in grievance_text.lower() for w in subject_words)

                if not already_mentioned:
                    q = self._create_question(
                        subject=subject,
                        dept=dept,
                        grievance_text=grievance_text,
                        is_telugu=is_telugu
                    )
                    if q:
                        questions.append(q)

        # Add grievance-type based questions
        type_questions = self._generate_type_questions(
            grievance_text, predicted_dept, is_telugu
        )
        questions.extend(type_questions)

        # Sort by relevance and dedupe
        questions = self._rank_and_dedupe(questions, grievance_text)

        return questions[:4]  # Return top 4

    def _create_question(
        self,
        subject: str,
        dept: str,
        grievance_text: str,
        is_telugu: bool
    ) -> Optional[Dict]:
        """Create a clarifying question for a subject."""
        # Question templates
        templates_en = {
            "Crop Insurance": ("Is this about crop insurance claim or premium?", "పంట బీమా క్లెయిమ్ గురించా?"),
            "Fertilizer Distribution": ("Is this about fertilizer availability or subsidy?", "ఎరువుల లభ్యత గురించా?"),
            "Agriculture Loans": ("Is this about agricultural loan or debt waiver?", "వ్యవసాయ రుణం గురించా?"),
            "Ration Card": ("Is this about ration card issue or new application?", "రేషన్ కార్డు సమస్య గురించా?"),
            "Fair Price Shop": ("Is this about fair price shop or dealer?", "ఫెయిర్ ప్రైస్ షాప్ సమస్య గురించా?"),
            "Rice Distribution": ("Is this about rice or food grain distribution?", "బియ్యం పంపిణీ సమస్య గురించా?"),
            "Old Age Pension": ("Is this about old age pension?", "వృద్ధాప్య పెన్షన్ గురించా?"),
            "Widow Pension": ("Is this about widow pension?", "వితంతు పెన్షన్ గురించా?"),
            "Disability Pension": ("Is this about disability pension?", "వికలాంగ పెన్షన్ గురించా?"),
            "Scholarship Issues": ("Is this about scholarship or fee reimbursement?", "స్కాలర్‌షిప్ గురించా?"),
            "Road Repair": ("Is this about road repair or potholes?", "రోడ్డు మరమ్మత్తు గురించా?"),
            "Drainage": ("Is this about drainage or sanitation?", "డ్రైనేజీ సమస్య గురించా?"),
            "Water Supply": ("Is this about drinking water supply?", "తాగునీటి సరఫరా గురించా?"),
            "Electricity": ("Is this about power supply or electricity bill?", "విద్యుత్ సరఫరా గురించా?"),
            "FIR": ("Is this about filing an FIR or police complaint?", "ఎఫ్‌ఐఆర్ నమోదు గురించా?"),
            "Theft": ("Is this about theft or robbery?", "దొంగతనం గురించా?"),
            "Harassment": ("Is this about harassment or safety?", "వేధింపు గురించా?"),
            "Land Records": ("Is this about land records or patta?", "భూమి రికార్డులు గురించా?"),
            "Land Dispute": ("Is this about land boundary or ownership dispute?", "భూ వివాదం గురించా?"),
            "Hospital": ("Is this about government hospital services?", "ప్రభుత్వ ఆసుపత్రి గురించా?"),
            "Teacher": ("Is this about teacher attendance or school issues?", "టీచర్ హాజరు గురించా?"),
            "School Infrastructure": ("Is this about school building or facilities?", "స్కూల్ భవనం గురించా?"),
        }

        # Generic fallback
        if subject not in templates_en:
            q_en = f"Is this specifically about {subject.lower()}?"
            q_te = f"ఇది {subject} గురించా?"
        else:
            q_en, q_te = templates_en[subject]

        # Calculate relevance based on keyword overlap
        grievance_lower = grievance_text.lower()
        subject_words = subject.lower().split()
        overlap = sum(1 for w in subject_words if w in grievance_lower)
        relevance = 0.5 + (overlap * 0.2)  # Base 0.5 + 0.2 per matching word

        return {
            "question": q_en,
            "question_telugu": q_te,
            "target_dept": dept,
            "confidence_boost": 0.12 + (relevance * 0.05),
            "relevance_score": min(relevance, 1.0),
            "subject": subject
        }

    def _generate_type_questions(
        self,
        grievance_text: str,
        predicted_dept: str,
        is_telugu: bool
    ) -> List[Dict]:
        """Generate questions based on grievance types."""
        questions = []
        grievance_lower = grievance_text.lower()

        # Check for ambiguous situations
        type_questions = [
            {
                "triggers": ["not received", "didn't get", "pending", "raaledu", "రాలేదు"],
                "question": "Is this about a payment/money OR a document/certificate?",
                "question_telugu": "ఇది చెల్లింపు గురించా లేదా పత్రం గురించా?",
                "options": [
                    ("Payment/Money", "Social Welfare"),
                    ("Document/Certificate", "Revenue")
                ]
            },
            {
                "triggers": ["officer", "official", "adhikari", "అధికారి"],
                "question": "Is the issue about officer behavior OR a pending service?",
                "question_telugu": "అధికారి ప్రవర్తన గురించా లేదా పెండింగ్ సేవ గురించా?",
                "options": [
                    ("Officer Behavior", predicted_dept),
                    ("Pending Service", predicted_dept)
                ]
            },
            {
                "triggers": ["bribe", "corruption", "lanch", "లంచం", "money asked"],
                "question": "Did an officer demand money/bribe?",
                "question_telugu": "అధికారి లంచం అడిగారా?",
                "options": [
                    ("Yes, bribe demanded", "Police"),
                    ("No, just delay", predicted_dept)
                ]
            }
        ]

        for tq in type_questions:
            if any(t in grievance_lower for t in tq["triggers"]):
                questions.append({
                    "question": tq["question"],
                    "question_telugu": tq["question_telugu"],
                    "target_dept": predicted_dept,
                    "confidence_boost": 0.15,
                    "relevance_score": 0.85,
                    "is_choice": True,
                    "options": tq["options"]
                })

        return questions

    def _rank_and_dedupe(
        self,
        questions: List[Dict],
        grievance_text: str
    ) -> List[Dict]:
        """Rank questions by relevance and remove duplicates."""
        # Remove duplicates by question text
        seen = set()
        unique = []
        for q in questions:
            key = q["question"].lower()[:50]
            if key not in seen:
                seen.add(key)
                unique.append(q)

        # Sort by relevance score
        unique.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return unique


# Singleton instance
_generator = None


def get_clarifying_questions(
    grievance_text: str,
    predicted_dept: str,
    top_3_depts: List[Dict],
    confidence: float
) -> List[Dict]:
    """Get clarifying questions for a grievance."""
    global _generator
    if _generator is None:
        _generator = ClarifyingQuestionsGenerator()

    return _generator.generate_questions(
        grievance_text=grievance_text,
        predicted_dept=predicted_dept,
        top_3_depts=top_3_depts,
        confidence=confidence
    )


# Test
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("pension not received for 6 months", "Social Welfare"),
        ("road has potholes", "Municipal Administration"),
        ("officer asked for bribe", "Revenue"),
        ("నా పెన్షన్ రాలేదు", "Social Welfare"),
        ("theft in my house police not helping", "Police"),
    ]

    gen = ClarifyingQuestionsGenerator()

    for text, dept in test_cases:
        print(f"\n{'='*60}")
        print(f"Grievance: {text}")
        print(f"Predicted: {dept}")

        questions = gen.generate_questions(
            grievance_text=text,
            predicted_dept=dept,
            top_3_depts=[
                {"department": dept, "confidence": 0.65},
                {"department": "Revenue", "confidence": 0.15},
                {"department": "Police", "confidence": 0.10},
            ],
            confidence=0.65
        )

        print(f"Questions ({len(questions)}):")
        for q in questions:
            print(f"  - {q['question']}")
            print(f"    Telugu: {q['question_telugu']}")
            print(f"    Target: {q['target_dept']}, Boost: +{q['confidence_boost']:.0%}")
