"""
triage.py — Rules-Based Service Request Classifier

How it works:
1. Takes the description text from a citizen's service request
2. Scans for keywords to determine the category
3. Scans for urgency signals to determine the priority
4. Returns a recommended next action based on category + priority

Design decision: deterministic keyword matching is used instead of
ML because it is fully explainable, testable, and documentable —
all three properties required for this submission. It can be swapped
for an LLM-based classifier in production without changing the
interface (same inputs, same outputs).
"""

# ── CATEGORY KEYWORD MAP ──────────────────────────────────────────
# Each category maps to a list of keywords that signal that category
# The classifier scans the description text for any of these words
CATEGORY_KEYWORDS = {
    "safety": [
        "danger", "dangerous", "emergency", "fire", "accident",
        "injury", "injured", "hazard", "hazardous", "unsafe",
        "threat", "violence", "crime", "flood", "gas leak",
        "electrical", "exposed wire", "collapsed", "collapse"
    ],
    "maintenance": [
        "streetlight", "street light", "pothole", "broken",
        "damaged", "repair", "road", "sidewalk", "crack",
        "cracked", "fallen", "tree", "branch", "sign",
        "traffic light", "signal", "bench", "fence", "graffiti"
    ],
    "sanitation": [
        "trash", "garbage", "waste", "litter", "dumping",
        "illegal dump", "smell", "sewage", "drain", "overflow",
        "rodent", "rats", "pest", "dirty", "filthy", "spill"
    ],
    "facility": [
        "park", "building", "restroom", "bathroom", "playground",
        "recreation", "community center", "library", "pool",
        "field", "court", "facility", "maintenance request"
    ],
    "IT": [
        "website", "portal", "system", "login", "access",
        "password", "app", "application", "online", "internet",
        "computer", "software", "technical", "error", "bug"
    ]
}

# ── PRIORITY KEYWORD MAP ──────────────────────────────────────────
# Keywords that signal urgency level
PRIORITY_KEYWORDS = {
    "critical": [
        "emergency", "fire", "injury", "injured", "danger",
        "dangerous", "gas leak", "exposed wire", "collapsed",
        "flood", "accident", "immediately", "urgent", "critical"
    ],
    "high": [
        "broken", "damaged", "unsafe", "hazard", "blocking",
        "blocked", "spill", "overflow", "no water", "no power",
        "illegal dump", "violence", "crime"
    ],
    "medium": [
        "pothole", "crack", "graffiti", "trash", "garbage",
        "rodent", "rats", "pest", "fallen", "tree", "branch",
        "smell", "dirty"
    ],
    "low": [
        "park", "bench", "sign", "playground", "website",
        "portal", "login", "password", "request", "inquiry"
    ]
}

# ── RECOMMENDED ACTION MAP ────────────────────────────────────────
# Maps category + priority → a recommended action string
# Format: ACTION_MAP[category][priority]
ACTION_MAP = {
    "safety": {
        "critical": "Dispatch emergency response team immediately. Contact 911 if not already done.",
        "high":     "Alert safety department. Schedule on-site inspection within 4 hours.",
        "medium":   "Route to safety department. Schedule inspection within 24 hours.",
        "low":      "Log for safety review. Schedule inspection within 72 hours."
    },
    "maintenance": {
        "critical": "Dispatch repair crew immediately. Block off area if needed.",
        "high":     "Schedule repair crew within 24 hours. Flag as priority work order.",
        "medium":   "Schedule repair crew within 72 hours.",
        "low":      "Add to next scheduled maintenance cycle."
    },
    "sanitation": {
        "critical": "Dispatch sanitation emergency crew immediately.",
        "high":     "Schedule sanitation crew within 24 hours.",
        "medium":   "Route to sanitation department. Schedule within 72 hours.",
        "low":      "Add to next scheduled sanitation route."
    },
    "facility": {
        "critical": "Dispatch facilities emergency team immediately.",
        "high":     "Alert facilities manager. Schedule repair within 24 hours.",
        "medium":   "Route to facilities department. Schedule within one week.",
        "low":      "Log for next scheduled facilities maintenance review."
    },
    "IT": {
        "critical": "Escalate to IT emergency support immediately.",
        "high":     "Route to IT help desk. Priority ticket — respond within 4 hours.",
        "medium":   "Submit IT help desk ticket. Respond within 24 hours.",
        "low":      "Log IT request. Address in next support cycle."
    },
    "general": {
        "critical": "Escalate immediately — review and route to appropriate department.",
        "high":     "Review and route to appropriate department within 4 hours.",
        "medium":   "Review and route to appropriate department within 24 hours.",
        "low":      "Review and route to appropriate department within one week."
    }
}


def classify_request(description: str) -> dict:
    """
    Main triage function.

    Takes a service request description string.
    Returns a dict with: category, priority, recommended_action.

    Steps:
    1. Normalize text (lowercase for case-insensitive matching)
    2. Score each category by counting keyword matches
    3. Score each priority by counting keyword matches
    4. Pick the highest-scoring category and priority
    5. Look up the recommended action from ACTION_MAP
    6. Return all three values

    Args:
        description: The citizen's service request description text

    Returns:
        {
            "category": str,
            "priority": str,
            "recommended_action": str
        }
    """
    # Step 1 — normalize to lowercase for case-insensitive matching
    text = description.lower()

    # Step 2 — score each category
    # For each category, count how many of its keywords appear in the text
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        category_scores[category] = score

    # Step 3 — pick highest scoring category
    # If no keywords matched at all, default to "general"
    best_category = max(category_scores, key=category_scores.get)
    if category_scores[best_category] == 0:
        best_category = "general"

    # Step 4 — score each priority level
    priority_scores = {}
    for priority, keywords in PRIORITY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        priority_scores[priority] = score

    # Step 5 — pick highest scoring priority
    # Priority order matters — if tied, higher urgency wins
    priority_order = ["critical", "high", "medium", "low"]
    best_priority = "low"
    for p in priority_order:
        if priority_scores.get(p, 0) > 0:
            best_priority = p
            break

    # Step 6 — look up recommended action
    # Use best_category if it exists in ACTION_MAP, else fall back to "general"
    action_category = best_category if best_category in ACTION_MAP else "general"
    recommended_action = ACTION_MAP[action_category][best_priority]

    return {
        "category": best_category,
        "priority": best_priority,
        "recommended_action": recommended_action
    }
