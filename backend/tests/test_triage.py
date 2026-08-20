"""
test_triage.py — Tests for the rules-based triage classifier

Tests verify that known inputs always produce correct outputs.
This is especially important for the Gemini regeneration test —
if the docs are followed correctly, these tests must all pass.

Run with:
    cd backend
    pytest tests/ -v
"""

import pytest
from triage import classify_request


# ── CATEGORY TESTS ─────────────────────────────────────────────────

def test_classify_maintenance_streetlight():
    """Broken streetlight should classify as maintenance/high."""
    result = classify_request("There is a broken streetlight near 5th and Main")
    assert result["category"] == "maintenance"
    assert result["priority"] == "high"
    assert result["recommended_action"] is not None


def test_classify_maintenance_pothole():
    """Pothole report should classify as maintenance."""
    result = classify_request("Large pothole on Wilshire Blvd damaging vehicles")
    assert result["category"] == "maintenance"
    assert result["priority"] in ["medium", "high"]


def test_classify_safety_emergency():
    """Gas leak emergency should classify as safety/critical."""
    result = classify_request(
        "Gas leak near the community park, dangerous emergency situation"
    )
    assert result["category"] == "safety"
    assert result["priority"] == "critical"


def test_classify_safety_fire():
    """Fire report should classify as safety/critical."""
    result = classify_request("Fire detected near the building, emergency")
    assert result["category"] == "safety"
    assert result["priority"] == "critical"


def test_classify_sanitation():
    """Trash dumping should classify as sanitation."""
    result = classify_request(
        "Illegal garbage dumping on my street with rats everywhere"
    )
    assert result["category"] == "sanitation"
    assert result["priority"] is not None


def test_classify_facility():
    """Park restroom issue should classify as facility."""
    result = classify_request("The restroom in the park is broken and unusable")
    assert result["category"] == "facility"
    assert result["priority"] is not None


def test_classify_it():
    """Login issue should classify as IT."""
    result = classify_request(
        "Cannot login to the city portal, password not working"
    )
    assert result["category"] == "IT"
    assert result["priority"] == "low"


def test_classify_vague_defaults_to_general():
    """Vague description with no keywords should default to general."""
    result = classify_request("Something needs to be fixed somewhere")
    assert result["category"] == "general"
    assert result["priority"] == "low"


# ── RETURN STRUCTURE TESTS ──────────────────────────────────────────

def test_classify_returns_all_fields():
    """Classifier must always return category, priority, and recommended_action."""
    result = classify_request("broken streetlight")
    assert "category" in result
    assert "priority" in result
    assert "recommended_action" in result


def test_classify_priority_values():
    """Priority must always be one of the four valid values."""
    valid_priorities = ["low", "medium", "high", "critical"]
    result = classify_request("There is a dangerous gas leak emergency")
    assert result["priority"] in valid_priorities


def test_classify_category_values():
    """Category must always be one of the valid values."""
    valid_categories = [
        "maintenance", "safety", "sanitation", "facility", "IT", "general"
    ]
    result = classify_request("broken road near downtown")
    assert result["category"] in valid_categories


def test_classify_case_insensitive():
    """Classifier should work regardless of uppercase or lowercase input."""
    result_lower = classify_request("broken streetlight")
    result_upper = classify_request("BROKEN STREETLIGHT")
    assert result_lower["category"] == result_upper["category"]
    assert result_lower["priority"] == result_upper["priority"]


def test_recommended_action_not_empty():
    """Recommended action should never be an empty string."""
    result = classify_request("trash piling up on the street")
    assert result["recommended_action"] != ""
    assert len(result["recommended_action"]) > 10