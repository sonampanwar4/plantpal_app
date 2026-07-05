from typing import Optional
from schemas.photo import ImageDiagnosisResponse


def format_similar_cases(similar_cases_list: list) -> str:
    context_parts = []
    if similar_cases_list:
        for i, case in enumerate(similar_cases_list, 1):
            context_parts.append(f"""Similar Case {i} (similarity: {case['similarity_score']:.2f}):
                {case['diagnosis_text'][:300]}
                Outcome: {case.get('treatment_outcome', 'Unknown')}""")
    else:
        context_parts.append("No similar historical cases found.")

    similar_cases = "".join(context_parts)

    return similar_cases

def format_confidence(confidence: float) -> str:
    if confidence >= 0.8:
        emoji, text = "🎯", "High confidence"
    elif confidence >= 0.6:
        emoji, text = "✅", "Good confidence"
    elif confidence >= 0.4:
        emoji, text = "⚠️", "Moderate confidence"
    else:
        emoji, text = "❓", "Low confidence"
    return f"{emoji} **Analysis Confidence:** {text} ({confidence:.1%})"

def format_issues(identified_issues: dict) -> str:
    if identified_issues and any(identified_issues.values()):
        parts = ["\n🔍 **Issues Identified:**"]
        for issue in identified_issues.get("issues", []):
            parts.append(f"• {issue}")
        return '\n'.join(parts)
    return "\n✅ **Good News:** No major issues detected in this image!"

def format_recommendations(actions: dict) -> str:
    parts = []
    if not actions:
        return ""
    treatments = actions.get("treatments", [])
    prevention = actions.get("prevention", "")

    if treatments or prevention:
        parts.append("\n🚨 **Recommended Actions Needed:**")
    if treatments:
        parts.append("\n🚨 **Treatments:**")
        for i, t in enumerate(treatments[:3], 1):
            parts.append(f"{i}. {t}")
    if prevention:
        parts.append("\n🚨 **Prevention:**")
        parts.append(prevention)
    return '\n'.join(parts)

def generate_photo_diagnosis_summary(
        analysis_result: dict,
        user_context: Optional[str] = None
) -> str:
    parts = []

    # User context
    if user_context:
        parts.append(f"📸 **Photo Analysis** - Regarding your concern: \"{user_context}\"")
    else:
        parts.append("📸 **Photo Analysis Results**")

    # Confidence
    confidence = analysis_result.get("confidence_score", 0.0)
    parts.append(format_confidence(confidence))

    # Issues
    parts.append(format_issues(analysis_result.get("identified_issues", {})))

    # Recommendations
    parts.append(format_recommendations(analysis_result.get("recommended_actions", {})))

    # Analysis text
    analysis_text = analysis_result.get("diagnosis_text", "")
    parts.append(f"\n💭 **Analysis Summary:**\n{analysis_text}" if analysis_text else "")

    return '\n'.join(parts)

def format_diagnosis_data(diagnosis_data: dict) -> dict:
    """Safely retrieves diagnosis data from response."""
    return {
        "diagnosis_text": diagnosis_data.get("diagnosis_text", ""),
        "confidence_score": diagnosis_data.get("confidence", 0.0),
        "identified_issues": {"issues": diagnosis_data.get("issues", [])},
        "recommended_actions": {
            "treatments": diagnosis_data.get("treatment", []),
            "prevention": diagnosis_data.get("prevention", "")
        },
        "treatment_outcome": diagnosis_data.get("treatment_outcome", "failed").lower()
    }