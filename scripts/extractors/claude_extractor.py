"""
Claude API integration for intelligent data extraction
"""
import json
from typing import Dict, List, Optional
from anthropic import Anthropic
from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    EXTRACTION_PROMPT_TEMPLATE
)


class ClaudeExtractor:
    """Use Claude API to extract structured data from text"""

    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=api_key)
        self.model = CLAUDE_MODEL

    def extract_from_text(
        self,
        simulant_name: str,
        simulant_id: str,
        source_text: str
    ) -> Optional[Dict]:
        """
        Extract structured simulant data from source text using Claude

        Returns: Dict with extracted fields or None if extraction failed
        """
        try:
            # Truncate text if too long (Claude has token limits)
            max_text_length = 15000  # ~4000 tokens
            if len(source_text) > max_text_length:
                source_text = source_text[:max_text_length] + "...[truncated]"

            # Build prompt
            prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                simulant_name=simulant_name,
                simulant_id=simulant_id,
                source_text=source_text
            )

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text
            extracted_data = json.loads(response_text)

            return extracted_data

        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse Claude response as JSON: {e}")
            print(f"   Response: {response_text[:200]}")
            return None

        except Exception as e:
            print(f"⚠️  Claude API error: {e}")
            return None

    def extract_from_multiple_sources(
        self,
        simulant_name: str,
        simulant_id: str,
        sources: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Extract data from multiple sources

        Args:
            simulant_name: Name of the simulant
            simulant_id: ID of the simulant
            sources: List of {source, text, source_type} dicts

        Returns:
            List of extracted data dictionaries with source attribution
        """
        extractions = []

        for source in sources:
            source_text = source.get('text', '')
            if not source_text:
                continue

            print(f"   🤖 Extracting from: {source.get('source', 'unknown')[:50]}...")

            extracted = self.extract_from_text(
                simulant_name,
                simulant_id,
                source_text
            )

            if extracted:
                # Add source metadata
                extracted['_source'] = source.get('source', 'unknown')
                extracted['_source_type'] = source.get('source_type', 'unknown')
                extractions.append(extracted)

        print(f"   ✅ Extracted data from {len(extractions)}/{len(sources)} sources")
        return extractions


if __name__ == "__main__":
    # Test
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY environment variable to test")
    else:
        extractor = ClaudeExtractor()
        test_text = """
        JSC-1A is a lunar simulant produced by Orbitec, Inc.
        It was released in 2006 and over 30 metric tons were produced.
        The simulant is currently unavailable as production has stopped.
        It replicates the composition of lunar mare basalt.
        """

        result = extractor.extract_from_text("JSC-1A", "S047", test_text)
        print(json.dumps(result, indent=2))
