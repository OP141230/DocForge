"""DocumentBrief compliance checker (Phase 6).

The split matters and is deliberate:

* **Deterministic** requirements are measured, not guessed - required section
  presence, word-count targets, forbidden topics, outline order.
* **Qualitative** requirements (tone, audience fit, "professional but warm") are
  given to the model, and every result from the model is reported as
  ``needs_review`` or ``partially_met`` unless it says otherwise - a model's
  opinion is never presented as an objective pass.

``overall`` is the worst status among the requirements that were actually
assessed, so a single hard failure cannot be hidden by a pile of passes.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.core.database import Database
from app.models.document_brief import DocumentBrief
from app.models.document_ir import DocumentIR
from app.models.review import (
    COMPLIANCE_LABELS,
    ComplianceReport,
    ComplianceResult,
    ComplianceStatus,
)
from app.providers.base import AIProvider
from app.providers.factory import get_provider
from app.repositories.compliance_repository import ComplianceRepository
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.repositories.document_repository import DocumentRepository
from app.services.document_text import DocumentTextIndex, normalize
from app.services.research_service import tokens

LIMITATIONS = [
    "Word counts, section presence and forbidden topics are measured exactly.",
    "Tone, audience fit and writing style are subjective; those rows say Needs Manual "
    "Review unless a language model assessed them, and even then they are an opinion.",
    "Compliance describes the document as it is now; it is re-run rather than reused "
    "after edits.",
]

WORD_TARGETS = {
    "short": (300, 900),
    "brief": (300, 900),
    "medium": (800, 2000),
    "long": (1800, 5000),
    "extended": (1800, 5000),
}

_ORDER = {
    ComplianceStatus.NOT_MET: 0,
    ComplianceStatus.PARTIALLY_MET: 1,
    ComplianceStatus.NEEDS_REVIEW: 2,
    ComplianceStatus.MET: 3,
    ComplianceStatus.NOT_APPLICABLE: 4,
}


class ComplianceService:
    def __init__(
        self, db: Database, *, provider: Optional[AIProvider] = None
    ):
        self.db = db
        self.provider = provider or get_provider()
        self.documents = DocumentRepository(db)
        self.briefs = DocumentBriefRepository(db)
        self.checks = ComplianceRepository(db)

    async def check(
        self, document_id: str, user_id: str, *, use_ai: bool = True
    ) -> ComplianceReport:
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        index = DocumentTextIndex(document)
        brief = await self._load_brief(document, user_id)

        if brief is None:
            return ComplianceReport(
                document_id=document_id,
                overall=ComplianceStatus.NOT_APPLICABLE,
                results=[],
                limitations=["This document has no linked brief, so there is nothing to comply with."],
                document_fingerprint=index.fingerprint,
            )

        results: List[ComplianceResult] = []
        results.extend(self._section_results(document, brief))
        results.extend(self._length_result(index, brief))
        results.extend(self._forbidden_topic_results(index, brief))
        results.extend(self._point_coverage_results(index, brief))
        results.extend(self._outline_result(document, brief))
        results.extend(self._type_result(document, brief))

        qualitative = self._qualitative_requirements(brief)
        if qualitative:
            if use_ai:
                results.extend(await self._ai_results(index, brief, qualitative))
            else:
                results.extend(
                    ComplianceResult(
                        requirement=requirement,
                        status=ComplianceStatus.NEEDS_REVIEW,
                        explanation="Not assessed: AI checks were disabled for this run.",
                        method="manual",
                    )
                    for requirement in qualitative
                )

        overall = self._overall(results)
        report = ComplianceReport(
            document_id=document_id,
            brief_id=brief.id,
            brief_title=brief.title,
            overall=overall,
            results=results,
            limitations=list(LIMITATIONS),
            document_fingerprint=index.fingerprint,
            generated_at=datetime.utcnow(),
        )
        await self.checks.save(report, user_id)
        return report

    async def latest(self, document_id: str, user_id: str) -> Optional[ComplianceReport]:
        return await self.checks.latest(document_id, user_id)

    # ------------------------------------------------------------------
    # Deterministic checks
    # ------------------------------------------------------------------
    def _section_results(
        self, document: DocumentIR, brief: DocumentBrief
    ) -> List[ComplianceResult]:
        required = brief.required_sections or []
        if not required:
            return []
        titles = {normalize(section.title) for section in document.content}
        results = []
        for name in required:
            present = normalize(name) in titles
            results.append(
                ComplianceResult(
                    requirement=f"Include the section \"{name}\"",
                    status=ComplianceStatus.MET if present else ComplianceStatus.NOT_MET,
                    explanation=(
                        f"A section titled \"{name}\" exists."
                        if present
                        else f"No section titled \"{name}\" was found."
                    ),
                    section_title=name if present else None,
                    suggested_action=None if present else f"Add a section called \"{name}\".",
                )
            )
        return results

    def _length_result(
        self, index: DocumentTextIndex, brief: DocumentBrief
    ) -> List[ComplianceResult]:
        if not brief.desired_length:
            return []
        minimum, maximum = self._word_target(brief.desired_length)
        words = index.word_count
        if words < minimum:
            status = ComplianceStatus.PARTIALLY_MET if words >= minimum * 0.7 else ComplianceStatus.NOT_MET
            explanation = (
                f"The document has {words} words; \"{brief.desired_length}\" suggests "
                f"{minimum}-{maximum}."
            )
            action = "Expand the thinner sections or add the missing depth."
        elif words > maximum:
            status = ComplianceStatus.PARTIALLY_MET
            explanation = (
                f"The document has {words} words, above the {minimum}-{maximum} target for "
                f"\"{brief.desired_length}\"."
            )
            action = "Trim repetition or tighten the longest sections."
        else:
            status = ComplianceStatus.MET
            explanation = f"{words} words is within the {minimum}-{maximum} target."
            action = None
        return [
            ComplianceResult(
                requirement=f"Approximate length: {brief.desired_length}",
                status=status,
                explanation=explanation,
                suggested_action=action,
            )
        ]

    def _forbidden_topic_results(
        self, index: DocumentTextIndex, brief: DocumentBrief
    ) -> List[ComplianceResult]:
        text = normalize(index.full_text)
        results = []
        for topic in brief.topics_to_avoid or []:
            needle = normalize(topic)
            mentioned = bool(needle) and needle in text
            results.append(
                ComplianceResult(
                    requirement=f"Avoid covering \"{topic}\"",
                    status=ComplianceStatus.NOT_MET if mentioned else ComplianceStatus.MET,
                    explanation=(
                        f"The document mentions \"{topic}\", which the brief excludes."
                        if mentioned
                        else f"\"{topic}\" does not appear in the document."
                    ),
                    suggested_action=f"Remove or rewrite the passage covering \"{topic}\"."
                    if mentioned
                    else None,
                )
            )
        return results

    def _point_coverage_results(
        self, index: DocumentTextIndex, brief: DocumentBrief
    ) -> List[ComplianceResult]:
        document_tokens = tokens(index.full_text)
        if not document_tokens:
            return []
        results = []
        for point in brief.important_points or []:
            point_tokens = tokens(point)
            if not point_tokens:
                continue
            overlap = len(point_tokens & document_tokens) / len(point_tokens)
            if overlap >= 0.75:
                status = ComplianceStatus.MET
                explanation = "The document covers this point in its own words."
            elif overlap >= 0.4:
                status = ComplianceStatus.PARTIALLY_MET
                explanation = "Some of this point appears, but the coverage looks partial."
            else:
                status = ComplianceStatus.NEEDS_REVIEW
                explanation = (
                    "Word overlap is low. This is a heuristic: a point can be covered "
                    "without reusing its wording, so confirm it by reading."
                )
            results.append(
                ComplianceResult(
                    requirement=f"Cover the point: {point}",
                    status=status,
                    explanation=explanation,
                    suggested_action="Strengthen this point with an explicit discussion."
                    if status != ComplianceStatus.MET
                    else None,
                )
            )
        return results

    def _outline_result(
        self, document: DocumentIR, brief: DocumentBrief
    ) -> List[ComplianceResult]:
        if not brief.outline:
            return []
        expected = [normalize(item.title) for item in brief.outline]
        actual = {normalize(section.title) for section in document.content}
        missing = [title for title in expected if title not in actual]
        if not missing:
            status = ComplianceStatus.MET
            explanation = "Every approved outline heading appears in the document."
        elif len(missing) <= max(1, len(expected) // 3):
            status = ComplianceStatus.PARTIALLY_MET
            explanation = "These approved headings are missing: " + ", ".join(missing)
        else:
            status = ComplianceStatus.NOT_MET
            explanation = "Most approved headings are missing: " + ", ".join(missing[:6])
        return [
            ComplianceResult(
                requirement="Follow the approved outline",
                status=status,
                explanation=explanation,
                suggested_action="Restore the missing headings or re-approve a new outline."
                if missing
                else None,
            )
        ]

    def _type_result(
        self, document: DocumentIR, brief: DocumentBrief
    ) -> List[ComplianceResult]:
        declared = document.metadata.document_type
        if not declared or not brief.document_type:
            return []
        matches = normalize(declared) == normalize(brief.document_type)
        return [
            ComplianceResult(
                requirement=f"Use document type \"{brief.document_type}\"",
                status=ComplianceStatus.MET if matches else ComplianceStatus.PARTIALLY_MET,
                explanation=(
                    "The document type matches the brief."
                    if matches
                    else f"The document is recorded as \"{declared}\" but the brief asked for "
                    f"\"{brief.document_type}\"."
                ),
            )
        ]

    # ------------------------------------------------------------------
    # Qualitative checks (model-assisted, always labelled)
    # ------------------------------------------------------------------
    def _qualitative_requirements(self, brief: DocumentBrief) -> List[str]:
        requirements: List[str] = []
        if brief.tone:
            requirements.append(f"Use a {brief.tone} tone")
        if brief.audience:
            requirements.append(f"Address the intended audience: {brief.audience}")
        if brief.writing_style:
            requirements.append(f"Follow the requested writing style: {brief.writing_style}")
        if brief.purpose:
            requirements.append(f"Fulfil the document purpose: {brief.purpose}")
        if brief.additional_instructions:
            requirements.append(
                f"Follow the additional instruction: {brief.additional_instructions}"
            )
        return requirements

    async def _ai_results(
        self, index: DocumentTextIndex, brief: DocumentBrief, requirements: List[str]
    ) -> List[ComplianceResult]:
        payload = {
            "text": index.full_text[:20000],
            "requirements": requirements,
            "document_type": brief.document_type,
        }
        try:
            raw = await self.provider.assess_compliance(payload)
        except Exception:
            raw = None

        if not raw or not isinstance(raw.get("results"), list):
            return [
                ComplianceResult(
                    requirement=requirement,
                    status=ComplianceStatus.NEEDS_REVIEW,
                    explanation=(
                        "No automated assessor is configured, so this subjective requirement "
                        "was not evaluated."
                    ),
                    method="manual",
                )
                for requirement in requirements
            ]

        by_requirement = {}
        for item in raw["results"]:
            if isinstance(item, dict) and item.get("requirement"):
                by_requirement[normalize(str(item["requirement"]))] = item

        results = []
        for requirement in requirements:
            item = by_requirement.get(normalize(requirement))
            if not item:
                results.append(
                    ComplianceResult(
                        requirement=requirement,
                        status=ComplianceStatus.NEEDS_REVIEW,
                        explanation="The assessor did not return a verdict for this requirement.",
                        method="ai",
                    )
                )
                continue
            raw_status = str(item.get("status") or "").strip().lower()
            status = {
                "met": ComplianceStatus.PARTIALLY_MET,
                "partially_met": ComplianceStatus.PARTIALLY_MET,
                "not_met": ComplianceStatus.NOT_MET,
                "not_applicable": ComplianceStatus.NOT_APPLICABLE,
                "needs_review": ComplianceStatus.NEEDS_REVIEW,
            }.get(raw_status, ComplianceStatus.NEEDS_REVIEW)
            results.append(
                ComplianceResult(
                    requirement=requirement,
                    status=status,
                    explanation=(str(item.get("explanation") or "").strip())[:1000]
                    or "The assessor gave no explanation.",
                    suggested_action=str(item.get("suggested_action") or "").strip() or None,
                    method="ai",
                )
            )
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _word_target(self, desired: str) -> Tuple[int, int]:
        lowered = desired.strip().lower()
        digits = re.findall(r"\d+", lowered)
        if digits:
            value = int(digits[0])
            if "page" in lowered:
                return max(100, value * 250), value * 400
            return int(value * 0.85), int(value * 1.15)
        for key, bounds in WORD_TARGETS.items():
            if key in lowered:
                return bounds
        return WORD_TARGETS["medium"]

    def _overall(self, results: List[ComplianceResult]) -> ComplianceStatus:
        assessed = [r.status for r in results if r.status != ComplianceStatus.NOT_APPLICABLE]
        if not assessed:
            return ComplianceStatus.NOT_APPLICABLE
        worst = min(assessed, key=lambda status: _ORDER[status])
        return worst

    async def _load_brief(
        self, document: DocumentIR, user_id: str
    ) -> Optional[DocumentBrief]:
        custom = document.metadata.custom_fields or {}
        brief_id = custom.get("brief_id")
        if brief_id:
            brief = await self.briefs.get_by_id(brief_id, user_id)
            if brief:
                return brief
        briefs, _ = await self.briefs.list_by_user(user_id, limit=200)
        return next((brief for brief in briefs if brief.document_id == document.id), None)


__all__ = ["ComplianceService", "COMPLIANCE_LABELS"]
