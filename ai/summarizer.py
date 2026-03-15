from __future__ import annotations

import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from transformers import AutoTokenizer, pipeline


MAX_INITIAL_CHARS = 16000
MAX_CHUNK_TOKENS = 950
MIN_SUMMARIZE_TOKENS = 200
MAX_WORKERS = 4
SUMMARY_MAX_LENGTH = 300
SUMMARY_MIN_LENGTH = 120

# Load the summarization pipeline once and reuse it across requests.
SUMMARIZER = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    tokenizer="facebook/bart-large-cnn",
    device=-1,
)
BART_TOKENIZER = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")


class LegalDocumentSummarizer:
    whitespace_pattern = re.compile(r"[ \t]+")
    repeated_newlines_pattern = re.compile(r"\n{3,}")
    page_number_pattern = re.compile(r"(?im)^\s*(?:page\s+)?\d+(?:\s+of\s+\d+)?\s*$")
    sentence_split_pattern = re.compile(r"(?<=[.!?])\s+")
    money_pattern = re.compile(r"(?:₹\s?\d[\d,]*(?:\.\d{1,2})?|Rs\.?\s?\d[\d,]*(?:\.\d{1,2})?|\$\s?\d[\d,]*(?:\.\d{1,2})?)")
    location_pattern = re.compile(
        r"(?i)\b(?:at|in|from|located at|executed at|court of)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\b"
    )
    party_pattern = re.compile(
        r"\b([A-Z][A-Za-z&.,'-]+(?:\s+[A-Z][A-Za-z&.,'-]+){0,5}\s+(?:Pvt\. Ltd\.|Ltd\.|LLP|Corporation|Company|Enterprises|Solutions))\b"
    )
    numbered_party_pattern = re.compile(
        r"(?im)^\s*\d+\.\s*([A-Z][A-Za-z&., ]+?(?:Pvt\. Ltd\.|Ltd\.|LLP|Corporation|Company|Enterprises|Solutions))\s*$"
    )
    designation_pattern = re.compile(
        r'(?im)^\s*([A-Z][A-Za-z&., ]+?)\s*\((?:hereinafter\s+referred\s+to\s+as\s+the\s+)?["“]?(First Party|Second Party|Partner A|Partner B)["”]?\)\s*$'
    )
    generic_party_phrases = {"agreement", "discussion", "discussions", "clause", "section", "parties", "supersedes"}
    clause_keywords = {
        "Capital Contribution": ("capital contribution", "capital requirement", "capital commitment"),
        "Decision Making": ("decision making", "voting rights", "board approval"),
        "Payment Terms": ("payment", "fees", "consideration", "invoice"),
        "Confidentiality": ("confidentiality", "non-disclosure", "nda"),
        "Termination": ("termination", "terminate", "expiry"),
        "Governing Law": ("governing law", "jurisdiction", "applicable law"),
        "Dispute Resolution": ("arbitration", "dispute resolution", "mediation"),
        "Indemnity": ("indemnity", "indemnify"),
        "Liability": ("liability", "limitation of liability"),
        "Scope of Work": ("scope of work", "services", "deliverables"),
        "Intellectual Property": ("intellectual property", "ip rights", "ownership"),
        "Compliance Obligations": ("compliance", "regulatory", "statutory"),
    }
    document_type_keywords = (
        ("Non-Disclosure Agreement", ("non-disclosure", "confidentiality agreement", "nda")),
        ("Partnership Agreement", ("partnership", "partners", "partner a", "partner b")),
        ("Service Agreement", ("service agreement", "services agreement", "scope of work")),
        ("Employment Agreement", ("employment agreement", "employee", "employer")),
        ("Lease Agreement", ("lease", "lessor", "lessee", "rent")),
        ("Memorandum of Understanding", ("memorandum of understanding", "mou")),
        ("Court Order", ("court order", "ordered that", "petition", "respondent")),
        ("Judgment", ("judgment", "justice", "court", "appellant")),
        ("Legal Agreement", ("agreement", "party", "parties")),
    )
    risk_patterns = (
        ("High capital requirement", ("high capital", "capital contribution", "capital requirement")),
        ("Liability exposure", ("liability", "damages", "losses")),
        ("Weak indemnity protection", ("indemnity", "indemnify")),
        ("Unilateral decision rights", ("sole discretion", "unilateral", "exclusive control")),
        ("Termination uncertainty", ("termination", "without cause", "immediate termination")),
        ("Compliance burden", ("compliance", "regulatory", "statutory obligation")),
    )

    def preprocess_text(self, text: str) -> str:
        limited_text = text[:MAX_INITIAL_CHARS]
        raw_lines = limited_text.splitlines()
        normalized_lines = [self.whitespace_pattern.sub(" ", line).strip() for line in raw_lines]

        repeated_short_lines = {
            line
            for line, count in Counter(
                line.casefold()
                for line in normalized_lines
                if line and len(line) <= 80
            ).items()
            if count >= 3
        }

        lines: list[str] = []
        blank_run = False
        for raw_line in raw_lines:
            stripped = self.whitespace_pattern.sub(" ", raw_line).strip()
            if not stripped:
                if not blank_run:
                    lines.append("")
                blank_run = True
                continue

            lowered = stripped.casefold()
            if self.page_number_pattern.match(stripped):
                continue
            if lowered in repeated_short_lines and (
                stripped.isupper() or "page" in lowered or "confidential" in lowered or "draft" in lowered
            ):
                continue

            lines.append(stripped)
            blank_run = False

        normalized = "\n".join(lines)
        normalized = self.repeated_newlines_pattern.sub("\n\n", normalized)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        return normalized.strip()

    def split_document(self, text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> list[str]:
        cleaned = self.preprocess_text(text)
        if not cleaned:
            return []

        paragraphs = [paragraph.strip() for paragraph in cleaned.split("\n\n") if paragraph.strip()]
        if not paragraphs:
            return [cleaned]

        chunks: list[str] = []
        current_paragraphs: list[str] = []
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = self._token_count(paragraph)
            if current_paragraphs and current_tokens + paragraph_tokens > max_tokens:
                chunks.append("\n\n".join(current_paragraphs))
                current_paragraphs = [paragraph]
                current_tokens = paragraph_tokens
                continue

            current_paragraphs.append(paragraph)
            current_tokens += paragraph_tokens

        if current_paragraphs:
            chunks.append("\n\n".join(current_paragraphs))

        return chunks or [cleaned]

    def summarize_chunk(self, chunk: str, max_length: int = SUMMARY_MAX_LENGTH, min_length: int = SUMMARY_MIN_LENGTH) -> str:
        result = SUMMARIZER(
            chunk,
            max_length=max_length,
            min_length=min_length,
            truncation=True,
            do_sample=False,
        )
        return result[0]["summary_text"].strip()

    def _safe_summary(self, text: str, max_length: int = SUMMARY_MAX_LENGTH, min_length: int = SUMMARY_MIN_LENGTH) -> str:
        cleaned = self.preprocess_text(text)
        if not cleaned:
            return ""

        token_count = self._token_count(cleaned)
        if token_count < MIN_SUMMARIZE_TOKENS:
            return cleaned

        adjusted_max = min(max_length, max(min_length, token_count - 5))
        adjusted_min = min(min_length, max(40, adjusted_max - 120))

        try:
            return self.summarize_chunk(cleaned, max_length=adjusted_max, min_length=adjusted_min)
        except Exception:
            return self._fallback_summary(cleaned)

    def _fallback_summary(self, text: str, min_sentences: int = 3, max_sentences: int = 6) -> str:
        sentences = [item.strip() for item in self.sentence_split_pattern.split(text) if item.strip()]
        if not sentences:
            return text[:1200].strip()
        selected = sentences[: max(min_sentences, min(max_sentences, len(sentences)))]
        return " ".join(selected).strip()

    @lru_cache(maxsize=64)
    def _cached_summary(self, normalized_text: str) -> tuple[str, str, tuple[str, ...], dict, dict]:
        cleaned_text = self.preprocess_text(normalized_text)
        chunks = self.split_document(cleaned_text)
        if not chunks:
            empty_structure = self._build_structured_summary("", "", self._extract_structured_insights("", ""))
            return "", "", tuple(), self._extract_structured_insights("", ""), empty_structure

        chunk_sizes = [self._token_count(chunk) for chunk in chunks]
        print(f"number_of_chunks={len(chunks)}")
        print(f"chunk_size={chunk_sizes}")

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(chunks))) as executor:
            chunk_summaries = list(executor.map(self._summarize_chunk_stage, chunks))

        merged_chunk_summaries = "\n\n".join(summary for summary in chunk_summaries if summary.strip())
        final_summary = self._safe_summary(merged_chunk_summaries or cleaned_text)
        short_summary = self._create_short_summary(final_summary)
        insights = self._extract_structured_insights(cleaned_text, final_summary)
        structured_summary = self._build_structured_summary(cleaned_text, final_summary, insights)
        detailed_summary = self._format_structured_summary(structured_summary)

        print(f"summary_length={len(detailed_summary)}")

        return short_summary, detailed_summary, tuple(chunk_summaries), insights, structured_summary

    def summarize_document(self, text: str) -> dict:
        normalized_text = self.preprocess_text(text)
        short_summary, detailed_summary, chunk_summaries, insights, structured_summary = self._cached_summary(normalized_text)
        return {
            "summary": short_summary,
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "chunk_summaries": list(chunk_summaries),
            "chunk_count": len(chunk_summaries),
            "insights": insights,
            "structured_summary": structured_summary,
        }

    def _summarize_chunk_stage(self, chunk: str) -> str:
        token_count = self._token_count(chunk)
        if token_count < MIN_SUMMARIZE_TOKENS:
            return chunk.strip()
        return self._safe_summary(chunk)

    def _create_short_summary(self, final_summary: str) -> str:
        cleaned = self.preprocess_text(final_summary)
        if not cleaned:
            return ""
        sentences = [item.strip() for item in self.sentence_split_pattern.split(cleaned) if item.strip()]
        if len(sentences) <= 2:
            return cleaned
        return " ".join(sentences[:2]).strip()

    def _build_structured_summary(self, text: str, final_summary: str, insights: dict) -> dict:
        overview = final_summary or self._fallback_summary(text)
        key_parties = ", ".join(insights.get("parties_inferred", [])) or "No clear parties were inferred from the available text."

        important_terms_parts: list[str] = []
        if insights.get("document_type"):
            important_terms_parts.append(f"Document Type: {insights['document_type']}")
        if insights.get("locations"):
            important_terms_parts.append(f"Locations: {', '.join(insights['locations'])}")
        if insights.get("financial_terms"):
            important_terms_parts.append(f"Financial Terms: {', '.join(insights['financial_terms'])}")
        important_terms = " ".join(important_terms_parts) or "No material terms were clearly extracted."

        main_clauses = ", ".join(insights.get("important_clauses", [])) or "No major clause themes were confidently identified."

        conclusion = self._build_conclusion(final_summary, insights)

        return {
            "document_overview": overview,
            "key_parties": key_parties,
            "important_terms": important_terms,
            "main_clauses": main_clauses,
            "conclusion": conclusion,
        }

    def _format_structured_summary(self, structured_summary: dict) -> str:
        sections = [
            ("Document Overview", structured_summary.get("document_overview", "")),
            ("Key Parties", structured_summary.get("key_parties", "")),
            ("Important Terms", structured_summary.get("important_terms", "")),
            ("Main Clauses", structured_summary.get("main_clauses", "")),
            ("Conclusion", structured_summary.get("conclusion", "")),
        ]
        return "\n\n".join(f"{title}: {content}".strip() for title, content in sections if content).strip()

    def _build_conclusion(self, final_summary: str, insights: dict) -> str:
        sentences = [item.strip() for item in self.sentence_split_pattern.split(final_summary) if item.strip()]
        closing = sentences[-1] if sentences else ""
        if closing:
            return closing

        if insights.get("important_clauses"):
            return f"The document mainly turns on {', '.join(insights['important_clauses'][:3])}."
        return "The document should be reviewed alongside the full text for precise legal interpretation."

    def _extract_structured_insights(self, text: str, summary: str) -> dict:
        combined = self.preprocess_text("\n\n".join(part for part in (summary, text) if part))
        lowered = combined.casefold()

        return {
            "document_type": self._infer_document_type(lowered),
            "parties_inferred": self._extract_parties(combined),
            "locations": self._extract_locations(combined),
            "financial_terms": self._unique_values(self.money_pattern.findall(combined))[:4],
            "important_clauses": self._extract_clauses(lowered),
            "risk_flags": self._extract_risk_flags(lowered),
        }

    def _infer_document_type(self, lowered_text: str) -> str:
        for label, keywords in self.document_type_keywords:
            if any(keyword in lowered_text for keyword in keywords):
                return label
        return "Legal Document"

    def _extract_parties(self, text: str) -> list[str]:
        candidates = list(self.numbered_party_pattern.findall(text))
        candidates.extend(match.group(1) for match in self.designation_pattern.finditer(text))
        candidates.extend(self.party_pattern.findall(text))

        filtered: list[str] = []
        for candidate in candidates:
            normalized = self._normalize_phrase(candidate)
            if not normalized:
                continue
            tokens = normalized.split()
            lowered = normalized.casefold()
            if len(tokens) > 6:
                continue
            if any(token in lowered for token in self.generic_party_phrases):
                continue
            filtered.append(normalized)
        return self._unique_values(filtered)[:4]

    def _extract_locations(self, text: str) -> list[str]:
        return self._unique_values(self._normalize_phrase(match) for match in self.location_pattern.findall(text))[:4]

    def _extract_clauses(self, lowered_text: str) -> list[str]:
        clauses: list[str] = []
        for label, keywords in self.clause_keywords.items():
            if any(keyword in lowered_text for keyword in keywords):
                clauses.append(label)
        return clauses[:6]

    def _extract_risk_flags(self, lowered_text: str) -> list[str]:
        risks: list[str] = []
        for label, keywords in self.risk_patterns:
            if any(keyword in lowered_text for keyword in keywords):
                risks.append(label)
        return risks[:5]

    def _token_count(self, text: str) -> int:
        return len(BART_TOKENIZER.encode(text, add_special_tokens=False))

    def _normalize_phrase(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" .,:;-")
        return cleaned

    def _unique_values(self, values) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            normalized = self._normalize_phrase(value)
            if not normalized:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        return unique


legal_summarizer = LegalDocumentSummarizer()


def summarize_document(text: str) -> str:
    return legal_summarizer.summarize_document(text)["summary"]
