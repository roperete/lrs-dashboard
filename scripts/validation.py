"""
Multi-source validation and fact-checking for extracted data
"""
import json
from typing import Dict, List, Optional
from collections import Counter
from anthropic import Anthropic
from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_TOKENS,
    FACT_CHECK_PROMPT,
    MIN_SOURCES_REQUIRED,
    CONFIDENCE_THRESHOLD
)


class DataValidator:
    """Validate extracted data across multiple sources"""

    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        self.client = Anthropic(api_key=api_key) if api_key else None

    def validate_field(self, field_name: str, values: List[Optional[str]]) -> Dict:
        """
        Validate a single field across multiple sources

        Returns:
            {
                "value": resolved_value,
                "confidence": 0.0-1.0,
                "sources_agree": bool,
                "num_sources": int
            }
        """
        # Filter out None/null values
        non_null_values = [v for v in values if v not in [None, "", "null", "None"]]

        if not non_null_values:
            return {
                "value": None,
                "confidence": 0.0,
                "sources_agree": False,
                "num_sources": 0
            }

        # Count occurrences
        value_counts = Counter(non_null_values)
        most_common_value, count = value_counts.most_common(1)[0]

        # Calculate confidence based on agreement
        total_sources = len(non_null_values)
        agreement_ratio = count / total_sources
        confidence = agreement_ratio

        # Boost confidence if we have multiple sources
        if total_sources >= MIN_SOURCES_REQUIRED:
            confidence = min(1.0, confidence * 1.2)

        return {
            "value": most_common_value,
            "confidence": confidence,
            "sources_agree": agreement_ratio > 0.5,
            "num_sources": total_sources,
            "all_values": list(value_counts.keys()) if len(value_counts) > 1 else None
        }

    def validate_extraction(
        self,
        simulant_name: str,
        extractions: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Validate all fields from multiple extractions

        Args:
            simulant_name: Name of the simulant
            extractions: List of extraction dictionaries from different sources

        Returns:
            Dict of {field_name: validation_result}
        """
        if not extractions:
            return {}

        # Get all field names (excluding metadata)
        fields = set()
        for extraction in extractions:
            fields.update(k for k in extraction.keys() if not k.startswith('_'))

        # Validate each field
        validation_results = {}

        for field in fields:
            values = [extraction.get(field) for extraction in extractions]
            validation = self.validate_field(field, values)
            validation_results[field] = validation

        return validation_results

    def resolve_conflicts_with_claude(
        self,
        simulant_name: str,
        extractions: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Use Claude to intelligently resolve conflicts between sources

        This is more sophisticated than simple voting - Claude can understand
        context, recency, and authority of sources.
        """
        if not self.client:
            print("⚠️  Claude API not available for conflict resolution")
            return self.validate_extraction(simulant_name, extractions)

        try:
            # Format extracted data for Claude
            formatted_data = []
            for i, extraction in enumerate(extractions, 1):
                source = extraction.get('_source', f'Source {i}')
                data_str = json.dumps(
                    {k: v for k, v in extraction.items() if not k.startswith('_')},
                    indent=2
                )
                formatted_data.append(f"Source {i} ({source}):\n{data_str}")

            extracted_data_str = "\n\n".join(formatted_data)

            # Build prompt
            prompt = FACT_CHECK_PROMPT.format(
                simulant_name=simulant_name,
                num_sources=len(extractions),
                extracted_data=extracted_data_str
            )

            # Call Claude
            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=0.2,  # Lower for fact-checking
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text
            resolved_data = json.loads(response_text)

            return resolved_data

        except Exception as e:
            print(f"⚠️  Claude conflict resolution failed: {e}")
            # Fall back to simple validation
            return self.validate_extraction(simulant_name, extractions)

    def get_auto_fillable_fields(self, validation_results: Dict[str, Dict]) -> Dict[str, any]:
        """
        Get fields that can be automatically filled based on confidence thresholds

        Returns: Dict of {field_name: value} for high-confidence fields
        """
        auto_fill = {}

        for field, result in validation_results.items():
            confidence = result.get('confidence', 0.0)
            num_sources = result.get('num_sources', 0)
            value = result.get('value')

            # Auto-fill if:
            # 1. Confidence is high enough
            # 2. We have minimum required sources
            # 3. Value is not None
            if (confidence >= CONFIDENCE_THRESHOLD and
                num_sources >= MIN_SOURCES_REQUIRED and
                value is not None):

                auto_fill[field] = value

        return auto_fill

    def get_review_required_fields(self, validation_results: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Get fields that require manual review (low confidence or conflicts)

        Returns: Dict of {field_name: validation_result} for fields needing review
        """
        review_required = {}

        for field, result in validation_results.items():
            confidence = result.get('confidence', 0.0)
            num_sources = result.get('num_sources', 0)
            value = result.get('value')

            # Require review if:
            # 1. Low confidence
            # 2. Not enough sources
            # 3. Sources disagree
            if (confidence < CONFIDENCE_THRESHOLD or
                num_sources < MIN_SOURCES_REQUIRED or
                not result.get('sources_agree', False)):

                review_required[field] = result

        return review_required


if __name__ == "__main__":
    # Test
    validator = DataValidator()

    # Simulate extractions from 3 sources
    test_extractions = [
        {"institution": "Orbitec, Inc.", "availability": "Production stopped", "release_date": "2006"},
        {"institution": "Orbitec, Inc.", "availability": "Unavailable", "release_date": "2006"},
        {"institution": "Orbital Technologies", "availability": "Production stopped", "release_date": None}
    ]

    results = validator.validate_extraction("JSC-1A", test_extractions)
    print("Validation Results:")
    print(json.dumps(results, indent=2))

    auto_fill = validator.get_auto_fillable_fields(results)
    print(f"\nAuto-fillable fields: {auto_fill}")

    review = validator.get_review_required_fields(results)
    print(f"\nFields requiring review: {list(review.keys())}")
