"""
Validation Pipeline for Extraction Quality and Human Review

This module provides comprehensive validation of extraction results with
confidence scoring, quality metrics, and human review workflow integration.
"""

import json
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from app.extraction.models import StakeholderExtraction, ExtractedStakeholder, DocumentReference


class ValidationLevel(str, Enum):
    """Validation strictness levels"""
    BASIC = "basic"      # Essential validation only
    STANDARD = "standard"  # Recommended validation
    STRICT = "strict"    # Comprehensive validation


class IssueType(str, Enum):
    """Types of validation issues"""
    ERROR = "error"      # Critical issues that block processing
    WARNING = "warning"  # Issues that may need attention
    INFO = "info"       # Informational notes


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    type: IssueType
    category: str
    message: str
    stakeholder_name: Optional[str] = None
    field: Optional[str] = None
    suggestion: Optional[str] = None
    confidence_impact: float = 0.0  # How much this reduces confidence (0.0-1.0)


@dataclass
class ValidationReport:
    """Complete validation report for an extraction"""
    extraction_id: str
    document_id: str
    validation_level: ValidationLevel
    overall_score: float  # 0.0-1.0
    is_valid: bool
    issues: List[ValidationIssue]
    quality_metrics: Dict[str, Any]
    recommendations: List[str]
    requires_human_review: bool
    validated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            **asdict(self),
            "issues": [asdict(issue) for issue in self.issues],
            "validated_at": self.validated_at.isoformat()
        }


class ExtractionValidator:
    """
    Comprehensive validator for stakeholder extraction results
    """
    
    def __init__(self, config: Any = None):
        self.config = config
        
        # Validation thresholds
        self.confidence_thresholds = {
            ValidationLevel.BASIC: 0.3,
            ValidationLevel.STANDARD: 0.6,
            ValidationLevel.STRICT: 0.8
        }
        
        # Common stakeholder patterns for validation
        self.common_stakeholder_terms = {
            "employees", "staff", "workers", "team", "personnel",
            "customers", "clients", "users", "consumers", "buyers",
            "management", "executives", "leadership", "board", "directors",
            "shareholders", "investors", "stakeholders", "owners",
            "community", "public", "residents", "citizens", "neighbors",
            "partners", "suppliers", "vendors", "contractors", "consultants",
            "regulators", "government", "authorities", "agencies",
            "media", "press", "journalists", "reporters"
        }
    
    def validate_extraction(
        self, 
        extraction: StakeholderExtraction,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> ValidationReport:
        """
        Perform comprehensive validation of extraction results
        """
        
        issues = []
        quality_metrics = {}
        
        # 1. Basic structural validation
        issues.extend(self._validate_structure(extraction))
        
        # 2. Confidence validation
        issues.extend(self._validate_confidence(extraction, validation_level))
        
        # 3. Content quality validation
        issues.extend(self._validate_content_quality(extraction, validation_level))
        
        # 4. Reference validation
        issues.extend(self._validate_references(extraction, validation_level))
        
        # 5. Semantic validation
        if validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            issues.extend(self._validate_semantics(extraction))
        
        # 6. Consistency validation
        if validation_level == ValidationLevel.STRICT:
            issues.extend(self._validate_consistency(extraction))
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(extraction, issues)
        
        # Determine overall validation status
        error_count = sum(1 for issue in issues if issue.type == IssueType.ERROR)
        warning_count = sum(1 for issue in issues if issue.type == IssueType.WARNING)
        
        is_valid = error_count == 0
        overall_score = self._calculate_overall_score(extraction, issues, quality_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(extraction, issues, quality_metrics)
        
        # Determine if human review is required
        requires_human_review = self._requires_human_review(
            extraction, issues, quality_metrics, validation_level
        )
        
        return ValidationReport(
            extraction_id=f"{extraction.document_id}_{int(extraction.extracted_at.timestamp())}",
            document_id=extraction.document_id,
            validation_level=validation_level,
            overall_score=overall_score,
            is_valid=is_valid,
            issues=issues,
            quality_metrics=quality_metrics,
            recommendations=recommendations,
            requires_human_review=requires_human_review,
            validated_at=datetime.now()
        )
    
    def _validate_structure(self, extraction: StakeholderExtraction) -> List[ValidationIssue]:
        """Validate basic structural requirements"""
        issues = []
        
        # Check required fields
        if not extraction.document_id:
            issues.append(ValidationIssue(
                type=IssueType.ERROR,
                category="structure",
                message="Missing document ID",
                confidence_impact=1.0
            ))
        
        if not extraction.document_title:
            issues.append(ValidationIssue(
                type=IssueType.WARNING,
                category="structure",
                message="Missing document title"
            ))
        
        if not extraction.stakeholders:
            issues.append(ValidationIssue(
                type=IssueType.ERROR,
                category="structure",
                message="No stakeholders extracted",
                suggestion="Check if document contains stakeholder information",
                confidence_impact=1.0
            ))
        
        # Validate individual stakeholders
        for i, stakeholder in enumerate(extraction.stakeholders):
            if not stakeholder.name or not stakeholder.name.strip():
                issues.append(ValidationIssue(
                    type=IssueType.ERROR,
                    category="structure",
                    message=f"Stakeholder {i+1} has empty name",
                    confidence_impact=0.2
                ))
        
        return issues
    
    def _validate_confidence(
        self, 
        extraction: StakeholderExtraction, 
        validation_level: ValidationLevel
    ) -> List[ValidationIssue]:
        """Validate confidence scores"""
        issues = []
        threshold = self.confidence_thresholds[validation_level]
        
        # Overall extraction confidence
        if extraction.extraction_confidence < threshold:
            issues.append(ValidationIssue(
                type=IssueType.WARNING if validation_level == ValidationLevel.BASIC else IssueType.ERROR,
                category="confidence",
                message=f"Overall extraction confidence {extraction.extraction_confidence:.2f} below threshold {threshold}",
                suggestion="Consider manual review or re-extraction with different parameters"
            ))
        
        # Individual stakeholder confidence
        low_confidence_stakeholders = [
            s for s in extraction.stakeholders 
            if s.confidence_score < threshold
        ]
        
        if low_confidence_stakeholders:
            for stakeholder in low_confidence_stakeholders:
                issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category="confidence",
                    message=f"Low confidence for stakeholder: {stakeholder.name} ({stakeholder.confidence_score:.2f})",
                    stakeholder_name=stakeholder.name,
                    suggestion="Review source text and extraction context"
                ))
        
        return issues
    
    def _validate_content_quality(
        self, 
        extraction: StakeholderExtraction, 
        validation_level: ValidationLevel
    ) -> List[ValidationIssue]:
        """Validate content quality and completeness"""
        issues = []
        
        for stakeholder in extraction.stakeholders:
            # Check for suspiciously short names
            if len(stakeholder.name) < 2:
                issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category="content_quality",
                    message=f"Very short stakeholder name: '{stakeholder.name}'",
                    stakeholder_name=stakeholder.name,
                    suggestion="Verify this is a valid stakeholder identifier"
                ))
            
            # Check for suspiciously long names (potential extraction errors)
            if len(stakeholder.name) > 100:
                issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category="content_quality",
                    message=f"Very long stakeholder name: '{stakeholder.name[:50]}...'",
                    stakeholder_name=stakeholder.name,
                    suggestion="May contain extracted sentence instead of stakeholder name"
                ))
            
            # Check for numeric-only names (usually errors)
            if stakeholder.name.strip().isdigit():
                issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category="content_quality",
                    message=f"Numeric-only stakeholder name: '{stakeholder.name}'",
                    stakeholder_name=stakeholder.name,
                    suggestion="Verify this represents a valid stakeholder"
                ))
            
            # Check for missing context in strict mode
            if validation_level == ValidationLevel.STRICT:
                if not stakeholder.role and not stakeholder.concerns and not stakeholder.responsibilities:
                    issues.append(ValidationIssue(
                        type=IssueType.INFO,
                        category="content_quality",
                        message=f"Limited context for stakeholder: {stakeholder.name}",
                        stakeholder_name=stakeholder.name,
                        suggestion="Consider extracting role, concerns, or responsibilities"
                    ))
        
        return issues
    
    def _validate_references(
        self, 
        extraction: StakeholderExtraction, 
        validation_level: ValidationLevel
    ) -> List[ValidationIssue]:
        """Validate source references and provenance"""
        issues = []
        
        # Check for missing references
        missing_refs = [s for s in extraction.stakeholders if not s.name_reference]
        
        if missing_refs and validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            issues.append(ValidationIssue(
                type=IssueType.WARNING,
                category="references",
                message=f"{len(missing_refs)} stakeholders missing source references",
                suggestion="Add source text references for better provenance tracking"
            ))
        
        # Validate reference quality
        for stakeholder in extraction.stakeholders:
            if stakeholder.name_reference:
                ref = stakeholder.name_reference
                
                # Check if reference text actually contains stakeholder name
                if stakeholder.name.lower() not in ref.source_text.lower():
                    issues.append(ValidationIssue(
                        type=IssueType.WARNING,
                        category="references",
                        message=f"Reference text doesn't contain stakeholder name: {stakeholder.name}",
                        stakeholder_name=stakeholder.name,
                        suggestion="Verify reference accuracy"
                    ))
                
                # Check for very short reference text
                if len(ref.source_text) < 10:
                    issues.append(ValidationIssue(
                        type=IssueType.INFO,
                        category="references",
                        message=f"Very short reference text for: {stakeholder.name}",
                        stakeholder_name=stakeholder.name
                    ))
        
        return issues
    
    def _validate_semantics(self, extraction: StakeholderExtraction) -> List[ValidationIssue]:
        """Validate semantic consistency and logic"""
        issues = []
        
        # Check for potential duplicate stakeholders
        stakeholder_names = [s.name.lower().strip() for s in extraction.stakeholders]
        seen_names = set()
        duplicates = set()
        
        for name in stakeholder_names:
            if name in seen_names:
                duplicates.add(name)
            seen_names.add(name)
        
        if duplicates:
            issues.append(ValidationIssue(
                type=IssueType.WARNING,
                category="semantics",
                message=f"Potential duplicate stakeholders: {', '.join(duplicates)}",
                suggestion="Review for actual duplicates vs. different references to same entity"
            ))
        
        # Check for unrealistic stakeholder types
        for stakeholder in extraction.stakeholders:
            name_lower = stakeholder.name.lower()
            
            # Individual stakeholders shouldn't be common group terms
            if (stakeholder.stakeholder_type.value == "stakeholder:IndividualStakeholder" and
                any(term in name_lower for term in ["employees", "customers", "community", "staff"])):
                issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category="semantics",
                    message=f"'{stakeholder.name}' classified as Individual but appears to be a group",
                    stakeholder_name=stakeholder.name,
                    suggestion="Consider reclassifying as GroupStakeholder"
                ))
        
        return issues
    
    def _validate_consistency(self, extraction: StakeholderExtraction) -> List[ValidationIssue]:
        """Validate internal consistency (strict mode only)"""
        issues = []
        
        # Check consistency between extraction confidence and individual confidences
        individual_avg = sum(s.confidence_score for s in extraction.stakeholders) / len(extraction.stakeholders)
        confidence_diff = abs(extraction.extraction_confidence - individual_avg)
        
        if confidence_diff > 0.3:
            issues.append(ValidationIssue(
                type=IssueType.INFO,
                category="consistency",
                message=f"Large difference between overall and average individual confidence: {confidence_diff:.2f}",
                suggestion="Review confidence scoring consistency"
            ))
        
        # Check for consistent reference document IDs
        ref_doc_ids = set()
        for stakeholder in extraction.stakeholders:
            if stakeholder.name_reference:
                ref_doc_ids.add(stakeholder.name_reference.document_id)
        
        if len(ref_doc_ids) > 1:
            issues.append(ValidationIssue(
                type=IssueType.WARNING,
                category="consistency",
                message="References point to multiple document IDs",
                suggestion="Ensure all references are from the same document"
            ))
        elif ref_doc_ids and extraction.document_id not in ref_doc_ids:
            issues.append(ValidationIssue(
                type=IssueType.WARNING,
                category="consistency",
                message="Reference document IDs don't match extraction document ID",
                suggestion="Verify document ID consistency"
            ))
        
        return issues
    
    def _calculate_quality_metrics(
        self, 
        extraction: StakeholderExtraction, 
        issues: List[ValidationIssue]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for the extraction"""
        
        metrics = {
            "total_stakeholders": len(extraction.stakeholders),
            "avg_confidence": sum(s.confidence_score for s in extraction.stakeholders) / len(extraction.stakeholders) if extraction.stakeholders else 0,
            "stakeholders_with_roles": sum(1 for s in extraction.stakeholders if s.role),
            "stakeholders_with_concerns": sum(1 for s in extraction.stakeholders if s.concerns),
            "stakeholders_with_references": sum(1 for s in extraction.stakeholders if s.name_reference),
            "total_issues": len(issues),
            "error_count": sum(1 for issue in issues if issue.type == IssueType.ERROR),
            "warning_count": sum(1 for issue in issues if issue.type == IssueType.WARNING),
            "info_count": sum(1 for issue in issues if issue.type == IssueType.INFO),
            "completeness_score": 0.0,
            "reference_coverage": 0.0
        }
        
        # Calculate completeness score
        if extraction.stakeholders:
            role_coverage = metrics["stakeholders_with_roles"] / metrics["total_stakeholders"]
            concern_coverage = metrics["stakeholders_with_concerns"] / metrics["total_stakeholders"]
            ref_coverage = metrics["stakeholders_with_references"] / metrics["total_stakeholders"]
            
            metrics["completeness_score"] = (role_coverage + concern_coverage + ref_coverage) / 3
            metrics["reference_coverage"] = ref_coverage
        
        return metrics
    
    def _calculate_overall_score(
        self, 
        extraction: StakeholderExtraction, 
        issues: List[ValidationIssue], 
        quality_metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall validation score (0.0-1.0)"""
        
        # Start with extraction confidence
        base_score = extraction.extraction_confidence
        
        # Apply confidence impact from issues
        confidence_penalty = sum(issue.confidence_impact for issue in issues)
        confidence_penalty = min(confidence_penalty, 0.8)  # Cap penalty
        
        # Apply quality bonus/penalty
        completeness_bonus = quality_metrics["completeness_score"] * 0.1
        reference_bonus = quality_metrics["reference_coverage"] * 0.05
        
        # Apply issue penalties
        error_penalty = quality_metrics["error_count"] * 0.2
        warning_penalty = quality_metrics["warning_count"] * 0.05
        
        final_score = base_score - confidence_penalty + completeness_bonus + reference_bonus - error_penalty - warning_penalty
        
        return max(0.0, min(1.0, final_score))
    
    def _generate_recommendations(
        self, 
        extraction: StakeholderExtraction, 
        issues: List[ValidationIssue], 
        quality_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Low confidence recommendations
        if extraction.extraction_confidence < 0.7:
            recommendations.append("Consider re-processing with different LLM parameters or manual review")
        
        # Missing context recommendations
        if quality_metrics["completeness_score"] < 0.5:
            recommendations.append("Extract more stakeholder context (roles, concerns, responsibilities)")
        
        # Reference recommendations
        if quality_metrics["reference_coverage"] < 0.8:
            recommendations.append("Add source text references for better provenance tracking")
        
        # Error-specific recommendations
        if quality_metrics["error_count"] > 0:
            recommendations.append("Resolve critical validation errors before proceeding")
        
        # Add specific issue suggestions
        unique_suggestions = set()
        for issue in issues:
            if issue.suggestion and issue.suggestion not in unique_suggestions:
                recommendations.append(issue.suggestion)
                unique_suggestions.add(issue.suggestion)
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _requires_human_review(
        self, 
        extraction: StakeholderExtraction, 
        issues: List[ValidationIssue], 
        quality_metrics: Dict[str, Any], 
        validation_level: ValidationLevel
    ) -> bool:
        """Determine if extraction requires human review"""
        
        # Always require review for errors
        if quality_metrics["error_count"] > 0:
            return True
        
        # Low confidence requires review
        if extraction.extraction_confidence < 0.6:
            return True
        
        # High warning count requires review
        if quality_metrics["warning_count"] > 3:
            return True
        
        # Strict mode requirements
        if validation_level == ValidationLevel.STRICT:
            if quality_metrics["completeness_score"] < 0.7:
                return True
            if quality_metrics["reference_coverage"] < 0.8:
                return True
        
        return False


# Export main classes
__all__ = ["ExtractionValidator", "ValidationReport", "ValidationIssue", "ValidationLevel", "IssueType"]
