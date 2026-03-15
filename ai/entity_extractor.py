from __future__ import annotations

import re
from functools import lru_cache

from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline


MAX_NER_CHARS = 16000
NER_CHUNK_TOKENS = 850
NER_CHUNK_OVERLAP = 100

NER_PIPELINE = None
NER_TOKENIZER = None
NER_LOAD_FAILED = False


class LegalEntityExtractor:
    whitespace_pattern = re.compile(r"[ \t]+")
    repeated_newlines_pattern = re.compile(r"\n{3,}")
    page_number_pattern = re.compile(r"(?im)^\s*(?:page\s+)?\d+(?:\s+of\s+\d+)?\s*$")
    punctuation_cleanup_pattern = re.compile(r"[^\w\s.'&/-]+")
    numbered_party_pattern = re.compile(
        r"(?im)^\s*\d+\.\s*(?P<name>[A-Z][A-Za-z&.,\s]+?(?:Ltd\.|LLP|Pvt\. Ltd\.|Corporation|Company))\s*$"
    )
    party_designation_pattern = re.compile(
        r'(?im)^\s*(?P<name>[A-Z][A-Za-z&., ]+?)\s*\((?:hereinafter\s+referred\s+to\s+as\s+the\s+)?["“]?(?P<role>First Party|Second Party|Partner A|Partner B)["”]?\)\s*$'
    )
    party_designation_label_pattern = re.compile(
        r"(?im)^\s*(?P<role>First Party|Second Party|Partner A|Partner B)\s*[:\-]\s*(?P<name>[A-Z][A-Za-z&., ]+)\s*$"
    )

    party_block_pattern = re.compile(
        r"(?is)\bBETWEEN\b\s*[:\-]?\s*(?P<party1>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){0,5})\s+\bAND\b\s*[:\-]?\s*(?P<party2>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){0,5})(?=\n{2,}|\b(?:versus|vs\.?|before|coram|judgment|order)\b|$)"
    )
    party_inline_pattern = re.compile(
        r"(?i)\bBETWEEN\b\s*[:\-]?\s*(?P<party1>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){0,5})\s+\bAND\b\s*[:\-]?\s*(?P<party2>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){0,5})(?=[,.;\n]|$)"
    )
    first_party_parenthetical_pattern = re.compile(
        r"(?i)\b(?P<name>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){1,5})\s*\(\s*First\s+Party\s*\)"
    )
    second_party_parenthetical_pattern = re.compile(
        r"(?i)\b(?P<name>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){1,5})\s*\(\s*Second\s+Party\s*\)"
    )
    first_party_label_pattern = re.compile(
        r"(?im)^\s*First\s+Party\s*[:\-]\s*(?P<name>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){1,5})\s*$"
    )
    second_party_label_pattern = re.compile(
        r"(?im)^\s*Second\s+Party\s*[:\-]\s*(?P<name>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){1,5})\s*$"
    )
    caption_pattern = re.compile(
        r"(?im)^\s*(?P<left>[A-Z][A-Za-z0-9.&,'\-\s]+?)\s+v(?:s\.?|ersus)\s+(?P<right>[A-Z][A-Za-z0-9.&,'\-\s]+?)\s*$"
    )
    party_role_pattern = re.compile(
        r"(?im)^\s*(?P<name>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){1,5})\s+(?P<role>wife|husband|petitioner|respondent|plaintiff|defendant|appellant|claimant)\b"
    )

    judge_pattern = re.compile(
        r"(?i)\b(?:Justice|Hon'?ble +Justice|Hon'?ble +Mr\.? +Justice|Hon'?ble +Ms\.? +Justice|Judge) +(?P<name>[A-Z][A-Za-z.'-]+(?: +[A-Z][A-Za-z.'-]+){1,3})\b"
    )
    location_at_pattern = re.compile(
        r"(?i)\bat +(?P<location>[A-Z][A-Za-z]+(?: +[A-Z][A-Za-z]+){0,3})\b"
    )
    court_location_pattern = re.compile(
        r"(?i)\b(?:High Court|District Court|Court) +of +(?P<location>[A-Z][A-Za-z]+(?: +[A-Z][A-Za-z]+){0,3})\b"
    )
    known_location_pattern = re.compile(
        r"\b(?:New Delhi|Delhi|Mumbai|Bengaluru|Bangalore|Chennai|Kolkata|Hyderabad|Pune)\b"
    )
    case_number_pattern = re.compile(
        r"(?i)\b(?:Civil|Criminal)\s+Appeal\s+No\.?\s*[:\-]?\s*[A-Za-z0-9./-]+|(?:Case|Writ Petition|Revision Petition)\s*No\.?\s*[:\-]?\s*[A-Za-z0-9./-]+"
    )
    date_pattern = re.compile(
        r"(?i)\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})\b"
    )
    money_pattern = re.compile(r"(?:₹\s?\d[\d,]*(?:\.\d{1,2})?|Rs\.?\s?\d[\d,]*(?:\.\d{1,2})?|\$\s?\d[\d,]*(?:\.\d{1,2})?)")

    role_keywords = ("plaintiff", "defendant", "petitioner", "respondent", "appellant", "claimant", "wife", "husband")
    stop_tokens = {
        "between",
        "and",
        "before",
        "coram",
        "order",
        "judgment",
        "justice",
        "judge",
        "high",
        "court",
        "case",
        "civil",
        "criminal",
    }
    invalid_party_tokens = {
        "the",
        "this",
        "that",
        "these",
        "those",
        "agreement",
        "deed",
        "contract",
        "clause",
        "payment",
        "confidentiality",
        "termination",
        "governing",
        "law",
        "matrimonial",
        "life",
        "force",
        "effect",
        "petition",
        "appeal",
        "case",
        "court",
        "judgment",
        "order",
        "decree",
        "respondent",
        "petitioner",
        "plaintiff",
        "defendant",
        "supersedes",
        "discussion",
        "discussions",
        "section",
        "parties",
    }
    invalid_party_phrases = {"supersedes", "agreement", "discussion", "discussions", "clause", "section", "parties"}
    organization_markers = {"ltd", "limited", "llp", "inc", "corp", "company", "co", "association", "trust", "bank"}
    agreement_entity_markers = {
        "ltd",
        "pvt",
        "llp",
        "corporation",
        "company",
        "enterprises",
        "solutions",
    }
    party_role_priority = {
        "first party": 0,
        "second party": 1,
        "party 1": 2,
        "party 2": 3,
        "petitioner": 4,
        "respondent": 5,
        "plaintiff": 6,
        "defendant": 7,
        "appellant": 8,
        "claimant": 9,
    }

    def preprocess_text(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                lines.append("")
                continue
            if self.page_number_pattern.match(stripped):
                continue
            lines.append(self.whitespace_pattern.sub(" ", stripped))

        normalized = "\n".join(lines)
        normalized = self.repeated_newlines_pattern.sub("\n\n", normalized)
        return normalized.strip()

    def _get_ner_components(self):
        global NER_PIPELINE, NER_TOKENIZER, NER_LOAD_FAILED

        if NER_LOAD_FAILED:
            return None, None
        if NER_PIPELINE is not None and NER_TOKENIZER is not None:
            return NER_PIPELINE, NER_TOKENIZER

        try:
            model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER", local_files_only=True)
            NER_TOKENIZER = AutoTokenizer.from_pretrained("dslim/bert-base-NER", local_files_only=True)
            NER_PIPELINE = pipeline(
                "token-classification",
                model=model,
                tokenizer=NER_TOKENIZER,
                aggregation_strategy="simple",
                device=-1,
            )
        except Exception:
            NER_LOAD_FAILED = True
            return None, None

        return NER_PIPELINE, NER_TOKENIZER

    def split_into_chunks(self, text: str, max_tokens: int = NER_CHUNK_TOKENS) -> list[str]:
        normalized = self.preprocess_text(text)[:MAX_NER_CHARS]
        if not normalized:
            return []

        _, tokenizer = self._get_ner_components()
        if tokenizer is None:
            return [normalized]

        token_ids = tokenizer.encode(normalized, add_special_tokens=False)
        if len(token_ids) <= max_tokens:
            return [normalized]

        chunks: list[str] = []
        step = max_tokens - NER_CHUNK_OVERLAP
        for start in range(0, len(token_ids), step):
            chunk_ids = token_ids[start : start + max_tokens]
            if not chunk_ids:
                continue
            chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True).strip()
            if chunk_text:
                chunks.append(chunk_text)
            if start + max_tokens >= len(token_ids):
                break
        return chunks

    @lru_cache(maxsize=64)
    def _run_cached_ner(self, normalized_text: str) -> tuple[tuple[str, str], ...]:
        ner_pipeline, _ = self._get_ner_components()
        if ner_pipeline is None:
            return tuple()

        entity_pairs: list[tuple[str, str]] = []
        for chunk in self.split_into_chunks(normalized_text):
            try:
                for entity in ner_pipeline(chunk):
                    label = str(entity.get("entity_group", "")).upper()
                    word = str(entity.get("word", "")).strip()
                    if word:
                        entity_pairs.append((label, word))
            except Exception:
                return tuple()
        return tuple(entity_pairs)

    def extract_entities(self, text: str) -> dict:
        normalized_text = self.preprocess_text(text)
        entity_pairs = self._run_cached_ner(normalized_text)

        persons = self._extract_group(entity_pairs, {"PER", "PERSON"})
        organizations = self._extract_group(entity_pairs, {"ORG"})
        ner_locations = self._extract_group(entity_pairs, {"LOC", "GPE"})

        parties = self._extract_parties(normalized_text, persons, organizations)
        judges = self._unique_strings(
            self._regex_group(self.judge_pattern, normalized_text, "name")
            + self._judge_candidates(persons, normalized_text)
        )
        judges = [judge for judge in judges if self._is_plausible_person(judge)]
        locations = self._unique_locations(
            self._regex_group(self.location_at_pattern, normalized_text, "location")
            + self._regex_group(self.court_location_pattern, normalized_text, "location")
            + self.known_location_pattern.findall(normalized_text)
            + ner_locations
        )
        case_numbers = self._unique_values(self.case_number_pattern.findall(normalized_text))
        dates = self._unique_values(self.date_pattern.findall(normalized_text))
        money = self._unique_values(self.money_pattern.findall(normalized_text))

        return {
            "judges": judges,
            "parties": parties,
            "locations": locations,
            "dates": dates,
            "case_numbers": case_numbers,
            "money": money,
            "monetary_values": money,
        }

    def _extract_group(self, entity_pairs: tuple[tuple[str, str], ...], labels: set[str]) -> list[str]:
        return self._unique_strings([word for label, word in entity_pairs if label in labels])

    def _judge_candidates(self, persons: list[str], text: str) -> list[str]:
        candidates: list[str] = []
        lowered = text.lower()
        for person in persons:
            person_name = self._normalize_name(person)
            lowered_person = person_name.lower()
            if re.search(rf"\b(?:justice|judge)\s+{re.escape(lowered_person)}\b", lowered):
                candidates.append(person_name)
        return candidates

    def _extract_parties(self, text: str, persons: list[str], organizations: list[str]) -> list[dict]:
        agreement_parties = self._extract_agreement_parties(text)
        if agreement_parties:
            return agreement_parties[:4]

        parties: list[dict] = []

        for pattern in (self.party_block_pattern, self.party_inline_pattern):
            for match in pattern.finditer(text):
                parties.extend(
                    [
                        self._build_party(match.group("party1"), "Party 1"),
                        self._build_party(match.group("party2"), "Party 2"),
                    ]
                )

        for match in self.caption_pattern.finditer(text):
            parties.extend(
                [
                    self._build_party(match.group("left"), "Party 1"),
                    self._build_party(match.group("right"), "Party 2"),
                ]
            )

        for pattern, role in (
            (self.first_party_parenthetical_pattern, "First Party"),
            (self.second_party_parenthetical_pattern, "Second Party"),
            (self.first_party_label_pattern, "First Party"),
            (self.second_party_label_pattern, "Second Party"),
        ):
            for match in pattern.finditer(text):
                parties.append(self._build_party(match.group("name"), role))

        for match in self.party_role_pattern.finditer(text):
            parties.append(self._build_party(match.group("name"), match.group("role")))

        if not parties:
            fallback_names = persons[:4] + organizations[:4]
            for index, name in enumerate(fallback_names, start=1):
                parties.append(self._build_party(name, f"Party {index}"))

        return self._unique_parties(parties)[:4]

    def _extract_agreement_parties(self, text: str) -> list[dict]:
        parties: list[dict] = []
        numbered_names: list[str] = []

        for match in self.numbered_party_pattern.finditer(text):
            name = match.group("name")
            if self._is_valid_agreement_party_name(name):
                numbered_names.append(name)

        if numbered_names:
            default_roles = ("First Party", "Second Party", "Partner A", "Partner B")
            for index, name in enumerate(numbered_names[:4]):
                parties.append(self._build_party(name, default_roles[index]))

        for pattern in (self.party_designation_pattern, self.party_designation_label_pattern):
            for match in pattern.finditer(text):
                name = match.group("name")
                role = match.group("role")
                if self._is_valid_agreement_party_name(name):
                    parties.append(self._build_party(name, role))

        return self._unique_parties(parties)[:4]

    def _build_party(self, raw_name: str, raw_role: str) -> dict:
        role = self._normalize_role(raw_role)
        name = self._strip_role_suffix(raw_name, role)
        normalized_name = self._normalize_name(name)
        if not self._is_plausible_party_name(normalized_name):
            return {"name": "", "role": role}
        return {"name": normalized_name, "role": role}

    def _normalize_name(self, value: str) -> str:
        cleaned = self.punctuation_cleanup_pattern.sub(" ", value)
        cleaned = cleaned.replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;-/")
        cleaned = re.sub(
            r"(?i)\b(?:wife|husband|petitioner|respondent|plaintiff|defendant|appellant|claimant|party\s*\d+)\b$",
            "",
            cleaned,
        ).strip(" .,:;-/")
        if not cleaned:
            return ""

        tokens: list[str] = []
        for token in cleaned.split():
            lower_token = token.lower()
            if lower_token in self.stop_tokens:
                continue
            if lower_token == "llp":
                tokens.append("LLP")
                continue
            if lower_token == "ltd":
                tokens.append("Ltd.")
                continue
            if lower_token == "pvt":
                tokens.append("Pvt.")
                continue
            if token.isupper() and len(token) > 1:
                tokens.append(token)
            elif "." in token:
                normalized_token = ".".join(part.capitalize() for part in token.split(".") if part)
                if token.endswith(".") and normalized_token:
                    normalized_token = f"{normalized_token}."
                tokens.append(normalized_token)
            else:
                tokens.append(token.capitalize())

        return " ".join(tokens[:6]).strip()

    def _normalize_role(self, value: str) -> str:
        cleaned = self.punctuation_cleanup_pattern.sub(" ", value)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return "Party"
        if cleaned.lower() == "first party":
            return "First Party"
        if cleaned.lower() == "second party":
            return "Second Party"
        if cleaned.lower().startswith("party"):
            return cleaned.title().replace("1", "1").replace("2", "2")
        return " ".join(token.capitalize() for token in cleaned.split())

    def _strip_role_suffix(self, raw_name: str, role: str) -> str:
        if not raw_name:
            return raw_name
        if not role:
            return raw_name
        pattern = re.compile(rf"\b{re.escape(role)}\b$", re.IGNORECASE)
        return pattern.sub("", raw_name).strip()

    def _regex_group(self, pattern: re.Pattern[str], text: str, group_name: str) -> list[str]:
        matches: list[str] = []
        for match in pattern.finditer(text):
            value = self._normalize_location(match.group(group_name)) if group_name == "location" else self._normalize_name(match.group(group_name))
            if value:
                matches.append(value)
        return matches

    def _unique_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            normalized = self._normalize_name(value)
            if not normalized:
                continue
            key = normalized.casefold()
            if key not in seen:
                seen.add(key)
                unique_values.append(normalized)
        return unique_values

    def _unique_values(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            normalized = re.sub(r"\s+", " ", str(value)).strip(" .,;:")
            if not normalized:
                continue
            key = normalized.casefold()
            if key not in seen:
                seen.add(key)
                unique_values.append(normalized)
        return unique_values

    def _unique_locations(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            normalized = self._normalize_location(value)
            if not normalized:
                continue
            if not self._is_plausible_location(normalized):
                continue
            key = normalized.casefold()
            if key not in seen:
                seen.add(key)
                unique_values.append(normalized)
        return unique_values

    def _unique_parties(self, parties: list[dict]) -> list[dict]:
        normalized_parties = []
        for party in parties:
            name = self._normalize_name(str(party.get("name", "")))
            role = self._normalize_role(str(party.get("role", "")))
            if not name or not self._is_plausible_party_name(name):
                continue
            normalized_parties.append({"name": name, "role": role})

        specific_roles = {
            party["name"].casefold()
            for party in normalized_parties
            if not party["role"].lower().startswith("party ")
        }

        seen: set[tuple[str, str]] = set()
        unique_values: list[dict] = []
        for party in normalized_parties:
            name = party["name"]
            role = party["role"]
            if role.lower().startswith("party ") and name.casefold() in specific_roles:
                continue
            key = (name.casefold(), role.casefold())
            if key in seen:
                continue
            seen.add(key)
            unique_values.append({"name": name, "role": role})
        return sorted(
            unique_values,
            key=lambda party: (self.party_role_priority.get(party["role"].casefold(), 99), party["name"].casefold()),
        )

    def _normalize_location(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value).strip(" .,:;-")
        if not cleaned:
            return ""
        return " ".join(token.capitalize() for token in cleaned.split())

    def _is_plausible_person(self, value: str) -> bool:
        tokens = value.split()
        return len(tokens) >= 2 and all(token[0].isalpha() for token in tokens if token)

    def _is_plausible_location(self, value: str) -> bool:
        tokens = value.split()
        if not tokens:
            return False
        return len(tokens) <= 4 and all(len(token) > 2 for token in tokens)

    def _is_plausible_party_name(self, value: str) -> bool:
        tokens = [token for token in value.split() if token]
        if len(tokens) < 2 or len(tokens) > 6:
            return False

        lowered = [token.casefold().strip(".") for token in tokens]
        if any(token in self.invalid_party_tokens for token in lowered):
            return False
        if any(phrase in value.casefold() for phrase in self.invalid_party_phrases):
            return False

        if any(token in self.organization_markers for token in lowered):
            return True

        alpha_tokens = [token for token in tokens if any(char.isalpha() for char in token)]
        if len(alpha_tokens) < 2:
            return False

        return all(token[0].isalpha() for token in alpha_tokens)

    def _is_valid_agreement_party_name(self, value: str) -> bool:
        normalized = self._normalize_name(value)
        if not normalized:
            return False

        tokens = [token for token in normalized.split() if token]
        if len(tokens) < 2 or len(tokens) > 6:
            return False

        lowered_text = normalized.casefold()
        if any(phrase in lowered_text for phrase in self.invalid_party_phrases):
            return False

        lowered_tokens = [token.casefold().strip(".,") for token in tokens]
        if not any(token in self.agreement_entity_markers for token in lowered_tokens):
            return False

        return self._is_plausible_party_name(normalized)


legal_entity_extractor = LegalEntityExtractor()


def extract_entities(text: str) -> dict:
    return legal_entity_extractor.extract_entities(text)
