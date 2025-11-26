"""
Knowledge Graph Visualization for DHRUVA
=========================================
Creates interactive network graphs showing relationships between:
- Districts
- Departments
- Issue Types
- Officers
- Grievance Patterns

Uses pyvis for visualization - install with: pip install pyvis
"""

from typing import Dict, List, Optional
import json
from pathlib import Path

# Check if pyvis is available
PYVIS_AVAILABLE = False
try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    print("Warning: pyvis not installed. Run: pip install pyvis")


# ============================================================================
# REAL DATA FROM AP GOVERNMENT DOCUMENTS
# Source: docs/VISUAL_STORYTELLING_DATA.md and docs/reference/markdown/*.md
# ============================================================================

# District satisfaction data (from State Call Center 1100 Feedback Report)
DISTRICT_DATA = {
    "Kakinada": {"satisfaction": 2.61, "rank": 1, "category": "best"},
    "Konaseema": {"satisfaction": 2.42, "rank": 2, "category": "good"},
    "Parvathipuram Manyam": {"satisfaction": 2.35, "rank": 3, "category": "good"},
    "West Godavari": {"satisfaction": 2.28, "rank": 4, "category": "good"},
    "East Godavari": {"satisfaction": 2.15, "rank": 5, "category": "average"},
    "Krishna": {"satisfaction": 2.10, "rank": 6, "category": "average"},
    "Guntur": {"satisfaction": 1.95, "rank": 7, "category": "average"},
    "Prakasam": {"satisfaction": 1.85, "rank": 8, "category": "below_avg"},
    "Nellore": {"satisfaction": 1.78, "rank": 9, "category": "below_avg"},
    "Chittoor": {"satisfaction": 1.72, "rank": 10, "category": "below_avg"},
    "Kadapa": {"satisfaction": 1.68, "rank": 11, "category": "poor"},
    "Kurnool": {"satisfaction": 1.62, "rank": 12, "category": "poor"},
    "Visakhapatnam": {"satisfaction": 1.54, "rank": 13, "category": "poor"},
    "Ananthapur": {"satisfaction": 1.49, "rank": 14, "category": "worst"},
}

# Department performance data (from PGRS reports)
DEPARTMENT_DATA = {
    "Revenue (CCLA)": {
        "dissatisfaction": 77.73,
        "reopen_rate": 73.5,
        "grievances": 4116,
        "category": "critical"
    },
    "Survey & Land Records": {
        "dissatisfaction": 77.63,
        "reopen_rate": 68.0,
        "grievances": 890,
        "category": "critical"
    },
    "Roads & Buildings": {
        "dissatisfaction": 58.97,
        "reopen_rate": 45.0,
        "grievances": 535,
        "category": "high"
    },
    "Police": {
        "dissatisfaction": 58.85,
        "reopen_rate": 42.0,
        "grievances": 1326,
        "category": "high"
    },
    "Panchayati Raj": {
        "dissatisfaction": 48.51,
        "reopen_rate": 38.0,
        "grievances": 648,
        "category": "medium"
    },
    "Municipal Administration": {
        "dissatisfaction": 45.0,
        "reopen_rate": 35.0,
        "grievances": 688,
        "category": "medium"
    },
    "Health (Public)": {
        "dissatisfaction": 42.0,
        "reopen_rate": 32.0,
        "grievances": 913,
        "category": "medium"
    },
    "Education": {
        "dissatisfaction": 38.0,
        "reopen_rate": 28.0,
        "grievances": 522,
        "category": "low"
    },
    "Agriculture": {
        "dissatisfaction": 32.0,
        "reopen_rate": 25.0,
        "grievances": 558,
        "category": "low"
    },
    "Civil Supplies": {
        "dissatisfaction": 28.0,
        "reopen_rate": 22.0,
        "grievances": 96,
        "category": "good"
    },
}

# Officer lapse types (from Improper Redressal lapses.md)
LAPSE_TYPES = {
    "behavioral": [
        {"code": "L1", "type": "GRA scolded / used abusive language", "severity": "HIGH"},
        {"code": "L2", "type": "GRA threatened / pleaded / persuaded", "severity": "HIGH"},
        {"code": "L3", "type": "GRA took/asked for bribe", "severity": "CRITICAL"},
        {"code": "L4", "type": "GRA involved political persons", "severity": "HIGH"},
        {"code": "L5", "type": "GRA intentionally avoided work", "severity": "MEDIUM"},
    ],
    "procedural": [
        {"code": "L6", "type": "GRA did not speak directly with citizen", "severity": "MEDIUM"},
        {"code": "L7", "type": "GRA did not provide endorsement personally", "severity": "MEDIUM"},
        {"code": "L8", "type": "GRA did not spend time explaining", "severity": "LOW"},
        {"code": "L9", "type": "WRONG/BLANK/NOT RELATED endorsement", "severity": "HIGH"},
        {"code": "L10", "type": "Uploaded improper enquiry photo/report", "severity": "HIGH"},
        {"code": "L11", "type": "Forwarded to lower-level instead of resolving", "severity": "MEDIUM"},
        {"code": "L12", "type": "Closed stating 'not under jurisdiction'", "severity": "HIGH"},
    ]
}

# Issue categories (from PGRS Book)
ISSUE_CATEGORIES = {
    "Land & Revenue": {
        "subtypes": ["Land record corrections", "Survey disputes", "Encroachment", "Mutation delays"],
        "volume": "HIGH",
        "satisfaction": "LOW"
    },
    "Housing": {
        "subtypes": ["House site allocation", "Housing scheme", "Construction permission"],
        "volume": "HIGH",
        "satisfaction": "LOW"
    },
    "Utilities": {
        "subtypes": ["Water supply", "Power outages", "Drainage/sewage"],
        "volume": "MEDIUM",
        "satisfaction": "MEDIUM"
    },
    "Certificates": {
        "subtypes": ["Caste/income certificates", "Pension disbursement", "Ration card"],
        "volume": "MEDIUM",
        "satisfaction": "MEDIUM"
    },
    "Law & Order": {
        "subtypes": ["Police inaction", "Harassment", "Domestic disputes"],
        "volume": "LOW",
        "satisfaction": "LOW"
    },
}

# Officer performance data (from West Godavari Pre-Audit Report)
OFFICER_PERFORMANCE = {
    "Joint Director of Fisheries": {"improper_rate": 76.67, "district": "West Godavari"},
    "District Fisheries Officer": {"improper_rate": 72.41, "district": "West Godavari"},
    "Tahsildar, Poduru": {"improper_rate": 55.00, "district": "West Godavari"},
    "District Revenue Officer": {"improper_rate": 73.50, "district": "Ananthapur"},
    "MRO Gooty": {"improper_rate": 52.30, "district": "Ananthapur"},
}

# Key statistics
KEY_STATS = {
    "total_feedback_calls": 93892,
    "avg_satisfaction": 1.9,
    "false_closures": 173020,
    "dissatisfaction_2018": 78,
    "variance_best_worst": 74,
}


class GrievanceKnowledgeGraph:
    """
    Creates interactive knowledge graph visualizations for AP PGRS data.
    """

    def __init__(self):
        self.network = None

    def create_district_department_graph(self) -> str:
        """
        Creates a graph showing districts connected to departments
        with satisfaction/performance as edge weights.
        Returns HTML string for rendering.
        """
        if not PYVIS_AVAILABLE:
            return "<p>pyvis not installed. Run: pip install pyvis</p>"

        net = Network(
            height="650px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#111827",
            directed=False
        )
        net.barnes_hut(gravity=-4000, central_gravity=0.3, spring_length=220)

        # Color scheme with clear meaning
        district_colors = {
            "best": "#059669",      # dark green - excellent
            "good": "#10B981",      # green - good
            "average": "#F59E0B",   # orange - average
            "below_avg": "#F97316", # dark orange - needs attention
            "poor": "#EF4444",      # red - poor
            "worst": "#DC2626",     # dark red - critical
        }

        dept_colors = {
            "critical": "#DC2626",  # dark red - >70% dissatisfaction
            "high": "#F97316",      # orange - 50-70% dissatisfaction
            "medium": "#F59E0B",    # yellow - 40-50% dissatisfaction
            "low": "#10B981",       # green - 30-40% dissatisfaction
            "good": "#059669",      # dark green - <30% dissatisfaction
        }

        # Add central PGRS node with key stats
        net.add_node(
            "PGRS",
            label="AP PGRS\n(93,892 calls)",
            color="#1E40AF",
            size=55,
            title="ANDHRA PRADESH PGRS ANALYSIS\n\nData Source: State Call Center 1100\nFeedback Calls Analyzed: 93,892\nAverage Satisfaction: 1.9/5.0 (LOW)\nDissatisfaction Rate: 78%\n\nClick nodes to explore!",
            font={"size": 16, "color": "#ffffff"},
            shape="circle"
        )

        # Add district nodes with rank indicators
        # KEY CHANGE: Bigger node = Bigger problem (lower satisfaction = higher dissatisfaction)
        for district, data in DISTRICT_DATA.items():
            color = district_colors.get(data['category'], "#6B7280")

            # Calculate dissatisfaction (inverse of satisfaction on 5-point scale)
            # Satisfaction 1.5 → Dissatisfaction ~70%, Satisfaction 2.6 → Dissatisfaction ~48%
            dissatisfaction_pct = round((5.0 - data['satisfaction']) / 5.0 * 100, 1)

            # Create label showing dissatisfaction % for problem districts
            if data['rank'] >= 12:  # Bottom 3 - worst performers
                label = f"{district}\n({dissatisfaction_pct:.0f}% unhappy)"
                border_width = 4
            elif data['rank'] <= 3:  # Top 3 - best performers
                label = f"{district}\n(#{data['rank']} best)"
                border_width = 2
            else:
                label = district
                border_width = 1

            # Size reflects DISSATISFACTION (bigger = more problems = needs attention)
            # Lower satisfaction score → Higher dissatisfaction → Bigger node
            size = 20 + ((5.0 - data['satisfaction']) * 12)  # Range: ~28 to ~44

            # Performance indicator
            if data['satisfaction'] >= 2.4:
                perf_text = "GOOD - Above state average"
            elif data['satisfaction'] >= 2.0:
                perf_text = "AVERAGE - Monitor"
            elif data['satisfaction'] >= 1.7:
                perf_text = "POOR - Needs attention"
            else:
                perf_text = "CRITICAL - Immediate intervention needed"

            net.add_node(
                f"D_{district}",
                label=label,
                color=color,
                size=size,
                borderWidth=border_width,
                title=f"DISTRICT: {district}\n\nDissatisfaction: {dissatisfaction_pct:.1f}%\nSatisfaction Score: {data['satisfaction']}/5.0\nState Rank: #{data['rank']} of 14\n\nAssessment: {perf_text}\n\nSource: State Call Center 1100 Feedback",
                shape="dot"
            )
            # Connect to central - thicker line = more problems
            edge_width = 1 + ((5.0 - data['satisfaction']) * 1.5)
            net.add_edge("PGRS", f"D_{district}", width=edge_width, color="#93C5FD")

        # Add department nodes with full names and performance
        for dept, data in DEPARTMENT_DATA.items():
            color = dept_colors.get(data['category'], "#6B7280")

            # Critical departments get special styling
            if data['dissatisfaction'] > 70:
                border_width = 4
                label = f"{dept}\n({data['dissatisfaction']:.0f}%)"
            elif data['dissatisfaction'] > 55:
                border_width = 2
                label = f"{dept}\n({data['dissatisfaction']:.0f}%)"
            else:
                border_width = 1
                label = dept

            # Size based on grievance volume
            size = 22 + (data['grievances'] / 80)

            # Performance assessment
            if data['dissatisfaction'] > 70:
                perf_text = "CRITICAL - Immediate Action Required"
            elif data['dissatisfaction'] > 55:
                perf_text = "HIGH CONCERN - Needs Improvement"
            elif data['dissatisfaction'] > 45:
                perf_text = "MODERATE - Monitor Closely"
            else:
                perf_text = "ACCEPTABLE - Maintain Standards"

            net.add_node(
                f"DEPT_{dept}",
                label=label,
                color=color,
                size=size,
                borderWidth=border_width,
                title=f"DEPARTMENT: {dept}\n\nDissatisfaction Rate: {data['dissatisfaction']:.1f}%\nGrievance Reopen Rate: {data['reopen_rate']:.1f}%\nTotal Grievances: {data['grievances']:,}\n\nAssessment: {perf_text}",
                shape="box"
            )
            net.add_edge("PGRS", f"DEPT_{dept}", width=2, color="#FCA5A5")

        # Connect problem districts to problematic departments with explanations
        problem_connections = [
            ("D_Ananthapur", "DEPT_Revenue (CCLA)", "HOTSPOT: Revenue issues in worst-ranked district\n73.5% complaints reopened"),
            ("D_Ananthapur", "DEPT_Survey & Land Records", "HOTSPOT: Land disputes driving 77.6% dissatisfaction"),
            ("D_Visakhapatnam", "DEPT_Police", "ISSUE: Police complaints in major city\n58.8% dissatisfaction"),
            ("D_Kurnool", "DEPT_Roads & Buildings", "ISSUE: Infrastructure complaints\n58.9% dissatisfaction"),
        ]

        added_dept_nodes = {f"DEPT_{dept}" for dept in DEPARTMENT_DATA.keys()}
        added_district_nodes = {f"D_{d}" for d in DISTRICT_DATA.keys()}

        for src, dst, title in problem_connections:
            if src in added_district_nodes and dst in added_dept_nodes:
                net.add_edge(src, dst, color="#DC2626", width=4, title=title, dashes=True)

        return net.generate_html()

    def create_lapse_pattern_graph(self) -> str:
        """
        Creates a graph showing officer lapse types and their relationships.
        Shows the 12 government-classified failure patterns.
        """
        if not PYVIS_AVAILABLE:
            return "<p>pyvis not installed. Run: pip install pyvis</p>"

        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#111827",
            directed=True
        )
        net.barnes_hut(gravity=-3500, spring_length=250)

        # Central node
        net.add_node(
            "lapses",
            label="12 Officer Lapse Types",
            color="#1E40AF",
            size=50,
            title="Government-classified GRA (Grievance Redressal Authority) failure patterns\n\nSource: AP PGRS Audit Framework\nUsed to classify improper grievance handling",
            font={"size": 18, "color": "#ffffff"}
        )

        # Behavioral category with better description
        net.add_node(
            "behavioral",
            label="BEHAVIORAL\n(5 Types)",
            color="#DC2626",
            size=40,
            title="BEHAVIORAL LAPSES (5 Types)\n\nHuman behavior failures where officers:\n- Act unprofessionally\n- Abuse their position\n- Show negligence or misconduct\n\nThese are more serious as they involve deliberate misconduct."
        )
        net.add_edge("lapses", "behavioral", color="#DC2626", width=4)

        # Procedural category with better description
        net.add_node(
            "procedural",
            label="PROCEDURAL\n(7 Types)",
            color="#F59E0B",
            size=40,
            title="PROCEDURAL LAPSES (7 Types)\n\nProcess/system failures where officers:\n- Don't follow proper procedures\n- Submit incomplete work\n- Fail to communicate properly\n\nThese often indicate training gaps or workload issues."
        )
        net.add_edge("lapses", "procedural", color="#F59E0B", width=4)

        # Severity colors with clearer meaning
        severity_colors = {
            "CRITICAL": "#DC2626",  # Red - requires immediate action
            "HIGH": "#F59E0B",       # Orange - serious concern
            "MEDIUM": "#FBBF24",     # Yellow - needs attention
            "LOW": "#34D399"         # Green - minor issue
        }

        # Short descriptive labels for behavioral lapses
        behavioral_short_labels = {
            "L1": "Abusive\nLanguage",
            "L2": "Threatened/\nPressured",
            "L3": "BRIBE\nDEMANDED",
            "L4": "Political\nInterference",
            "L5": "Work\nAvoidance",
        }

        # Short descriptive labels for procedural lapses
        procedural_short_labels = {
            "L6": "No Direct\nContact",
            "L7": "No Personal\nEndorsement",
            "L8": "Poor\nExplanation",
            "L9": "Wrong/Blank\nEndorsement",
            "L10": "Improper\nPhoto/Report",
            "L11": "Improper\nForwarding",
            "L12": "False\nJurisdiction",
        }

        # Add behavioral lapses with descriptive labels
        for lapse in LAPSE_TYPES["behavioral"]:
            color = severity_colors.get(lapse["severity"], "#6B7280")
            short_label = behavioral_short_labels.get(lapse["code"], lapse["code"])

            # Size based on severity
            size_map = {"CRITICAL": 35, "HIGH": 28, "MEDIUM": 22, "LOW": 18}
            size = size_map.get(lapse["severity"], 20)

            net.add_node(
                lapse["code"],
                label=short_label,
                color=color,
                size=size,
                title=f"Code: {lapse['code']}\n\nDescription:\n{lapse['type']}\n\nSeverity: {lapse['severity']}\nCategory: Behavioral Lapse"
            )
            net.add_edge("behavioral", lapse["code"], color=color, width=2)

        # Add procedural lapses with descriptive labels
        for lapse in LAPSE_TYPES["procedural"]:
            color = severity_colors.get(lapse["severity"], "#6B7280")
            short_label = procedural_short_labels.get(lapse["code"], lapse["code"])

            size_map = {"CRITICAL": 35, "HIGH": 28, "MEDIUM": 22, "LOW": 18}
            size = size_map.get(lapse["severity"], 20)

            net.add_node(
                lapse["code"],
                label=short_label,
                color=color,
                size=size,
                title=f"Code: {lapse['code']}\n\nDescription:\n{lapse['type']}\n\nSeverity: {lapse['severity']}\nCategory: Procedural Lapse"
            )
            net.add_edge("procedural", lapse["code"], color=color, width=2)

        return net.generate_html()

    def create_issue_flow_graph(self) -> str:
        """
        Creates a graph showing issue categories and their flow through departments.
        Shows how citizen grievances flow from categories to responsible departments.
        """
        if not PYVIS_AVAILABLE:
            return "<p>pyvis not installed. Run: pip install pyvis</p>"

        net = Network(
            height="550px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#111827",
            directed=True
        )
        net.barnes_hut(gravity=-2500, spring_length=180)

        # Citizen node
        net.add_node(
            "citizen",
            label="93,892 Citizens",
            color="#10B981",
            size=50,
            title="AP Citizens filing grievances\n93,892 feedback calls analyzed\nSource: State Call Center 1100",
            shape="circle",
            font={"size": 16, "color": "#ffffff"}
        )

        # Issue categories with better labels
        volume_sizes = {"HIGH": 38, "MEDIUM": 30, "LOW": 22}
        satisfaction_colors = {"HIGH": "#10B981", "MEDIUM": "#F59E0B", "LOW": "#EF4444"}

        for category, data in ISSUE_CATEGORIES.items():
            size = volume_sizes.get(data["volume"], 25)
            color = satisfaction_colors.get(data["satisfaction"], "#6B7280")

            # Create clear label with volume indicator
            volume_icon = {"HIGH": "+++", "MEDIUM": "++", "LOW": "+"}
            label = f"{category}\n({volume_icon.get(data['volume'], '')})"

            net.add_node(
                f"cat_{category}",
                label=label,
                color=color,
                size=size,
                title=f"Issue Category: {category}\n\nVolume: {data['volume']} complaint volume\nCitizen Satisfaction: {data['satisfaction']}\n\nCommon Subtypes:\n- " + "\n- ".join(data['subtypes'])
            )
            net.add_edge("citizen", f"cat_{category}", width=2, color="#D1D5DB")

        # Connect to departments - track added nodes to avoid duplicates
        category_dept_map = {
            "Land & Revenue": ["Revenue (CCLA)", "Survey & Land Records"],
            "Housing": ["Municipal Administration", "Panchayati Raj"],
            "Utilities": ["Municipal Administration", "Health (Public)"],
            "Certificates": ["Revenue (CCLA)", "Civil Supplies"],
            "Law & Order": ["Police"],
        }

        added_dept_nodes = set()  # Track added department nodes

        for cat, depts in category_dept_map.items():
            for dept in depts:
                if dept in DEPARTMENT_DATA:
                    dept_data = DEPARTMENT_DATA[dept]
                    dept_node_id = f"dept_{dept}"

                    # Only add node if not already added
                    if dept_node_id not in added_dept_nodes:
                        # Color based on dissatisfaction level
                        if dept_data['dissatisfaction'] > 70:
                            dept_color = "#DC2626"  # Red - critical
                        elif dept_data['dissatisfaction'] > 50:
                            dept_color = "#F59E0B"  # Orange - high
                        else:
                            dept_color = "#3B82F6"  # Blue - moderate

                        net.add_node(
                            dept_node_id,
                            label=dept,
                            color=dept_color,
                            size=28,
                            title=f"Department: {dept}\n\nDissatisfaction Rate: {dept_data['dissatisfaction']:.1f}%\nReopen Rate: {dept_data['reopen_rate']:.1f}%\nTotal Grievances: {dept_data['grievances']:,}",
                            shape="box"
                        )
                        added_dept_nodes.add(dept_node_id)

                    net.add_edge(f"cat_{cat}", dept_node_id, color="#93C5FD", width=2)

        return net.generate_html()

    def create_performance_heatmap_graph(self) -> str:
        """
        Creates a graph showing officer performance patterns.
        Highlights officers with high improper redressal rates.
        """
        if not PYVIS_AVAILABLE:
            return "<p>pyvis not installed. Run: pip install pyvis</p>"

        net = Network(
            height="550px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#111827",
            directed=False
        )
        net.barnes_hut(gravity=-2500, spring_length=180)

        # Add central context node
        net.add_node(
            "audit",
            label="OFFICER AUDIT\nPre-Audit Findings",
            color="#1E40AF",
            size=50,
            title="OFFICER PERFORMANCE AUDIT\n\nSource: West Godavari & Ananthapur Pre-Audit Reports\n\nThis graph shows officers with HIGH improper redressal rates.\nThese officers need training or performance intervention.\n\nColor Key:\n- Red (>70%): Critical - Immediate action needed\n- Orange (50-70%): High concern - Training required\n- Yellow (<50%): Moderate - Monitor closely",
            font={"size": 14, "color": "#ffffff"},
            shape="circle"
        )

        # Districts as main nodes
        districts_with_officers = set(d["district"] for d in OFFICER_PERFORMANCE.values())

        for district in districts_with_officers:
            # Get district's satisfaction ranking
            dist_data = DISTRICT_DATA.get(district, {})
            rank = dist_data.get('rank', 'N/A')
            satisfaction = dist_data.get('satisfaction', 'N/A')

            net.add_node(
                f"dist_{district}",
                label=f"{district}\nDistrict",
                color="#6366F1",  # Indigo
                size=40,
                title=f"DISTRICT: {district}\n\nState Satisfaction Rank: #{rank}\nSatisfaction Score: {satisfaction}/5.0\n\nOfficers shown are those flagged\nin pre-audit reports.",
                shape="circle",
                font={"size": 12}
            )
            net.add_edge("audit", f"dist_{district}", color="#A5B4FC", width=2)

        # Officer nodes with more context
        for officer, data in OFFICER_PERFORMANCE.items():
            rate = data["improper_rate"]

            # Color and assessment based on improper rate
            if rate > 70:
                color = "#DC2626"  # Red - critical
                assessment = "CRITICAL - Immediate Training Required"
                border_width = 4
            elif rate > 50:
                color = "#F97316"  # Orange - high concern
                assessment = "HIGH CONCERN - Schedule Training"
                border_width = 3
            else:
                color = "#EAB308"  # Yellow - moderate
                assessment = "MODERATE - Monitor Performance"
                border_width = 2

            # Create clear label with rate
            officer_short = officer.split(',')[0]  # Remove district suffix if any
            label = f"{officer_short}\n({rate:.0f}% improper)"

            net.add_node(
                f"off_{officer}",
                label=label,
                color=color,
                size=25 + (rate / 4),
                borderWidth=border_width,
                title=f"OFFICER: {officer}\n\nImproper Redressal Rate: {rate:.1f}%\nDistrict: {data['district']}\n\nAssessment: {assessment}\n\nThis means {rate:.0f}% of grievances handled\nby this officer were found to be\nimproperly resolved in audit.",
                shape="box"
            )
            net.add_edge(f"dist_{data['district']}", f"off_{officer}", color=color, width=3)

        return net.generate_html()

    def get_summary_stats(self) -> Dict:
        """Returns key statistics for display."""
        return {
            "total_districts": len(DISTRICT_DATA),
            "total_departments": len(DEPARTMENT_DATA),
            "total_lapse_types": sum(len(v) for v in LAPSE_TYPES.values()),
            "total_issue_categories": len(ISSUE_CATEGORIES),
            "key_stats": KEY_STATS,
            "worst_district": min(DISTRICT_DATA.items(), key=lambda x: x[1]["satisfaction"]),
            "best_district": max(DISTRICT_DATA.items(), key=lambda x: x[1]["satisfaction"]),
            "worst_department": max(DEPARTMENT_DATA.items(), key=lambda x: x[1]["dissatisfaction"]),
        }


def check_pyvis_available() -> bool:
    """Check if pyvis is available."""
    return PYVIS_AVAILABLE


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("Knowledge Graph Module Test")
    print("=" * 60)

    print(f"\nPyvis available: {PYVIS_AVAILABLE}")

    if PYVIS_AVAILABLE:
        kg = GrievanceKnowledgeGraph()
        stats = kg.get_summary_stats()

        print(f"\nData Summary:")
        print(f"  Districts: {stats['total_districts']}")
        print(f"  Departments: {stats['total_departments']}")
        print(f"  Lapse Types: {stats['total_lapse_types']}")
        print(f"  Issue Categories: {stats['total_issue_categories']}")

        print(f"\nKey Statistics:")
        for k, v in stats['key_stats'].items():
            print(f"  {k}: {v}")

        print(f"\nBest District: {stats['best_district'][0]} (satisfaction: {stats['best_district'][1]['satisfaction']})")
        print(f"Worst District: {stats['worst_district'][0]} (satisfaction: {stats['worst_district'][1]['satisfaction']})")

        # Generate test HTML
        html = kg.create_district_department_graph()
        print(f"\nGenerated district-department graph: {len(html)} bytes")
    else:
        print("\nInstall pyvis with: pip install pyvis")
