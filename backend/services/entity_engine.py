from __future__ import annotations

import re

from backend.services.spacy_service import spacy_service


class EntityEngine:
    numbered_party_pattern = re.compile(
        r"(?im)^\s*\d+\.\s*(?P<name>[A-Z][A-Za-z&.,\s]+?(?:Ltd\.|LLP|Pvt\. Ltd\.|Corporation|Company))\s*$"
    )
    party_designation_pattern = re.compile(
        r'(?im)^\s*(?P<name>[A-Z][A-Za-z&., ]+?)\s*\((?:hereinafter\s+referred\s+to\s+as\s+the\s+)?["“]?(?P<role>First Party|Second Party|Partner A|Partner B)["”]?\)\s*$'
    )
    party_designation_label_pattern = re.compile(
        r"(?im)^\s*(?P<role>First Party|Second Party|Partner A|Partner B|Petitioner|Respondent|Plaintiff|Defendant)\s*[:\-]\s*(?P<name>[A-Z][A-Za-z&., ]+)\s*$"
    )
    party_block_pattern = re.compile(
        r"(?is)\bBETWEEN\b\s*[:\-]?\s*(?P<party1>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){0,5})\s+\bAND\b\s*[:\-]?\s*(?P<party2>[A-Z][A-Za-z.'&/-]+(?:\s+[A-Z][A-Za-z.'&/-]+){0,5})"
    )
    caption_pattern = re.compile(
        r"(?im)^\s*(?P<left>[A-Z][A-Za-z0-9.&,'\-\s]+?)\s+v(?:s\.?|ersus)\s+(?P<right>[A-Z][A-Za-z0-9.&,'\-\s]+?)\s*$"
    )
    judge_pattern = re.compile(
        r"(?i)\b(?:Justice|Hon'?ble +Justice|Hon'?ble +Mr\.? +Justice|Hon'?ble +Ms\.? +Justice|Judge) +(?P<name>[A-Z][A-Za-z.'-]+(?: +[A-Z][A-Za-z.'-]+){1,3})\b"
    )
    location_at_pattern = re.compile(r"(?i)\bat +(?P<location>[A-Z][A-Za-z]+(?: +[A-Z][A-Za-z]+){0,3})\b")
    court_location_pattern = re.compile(
        r"(?i)\b(?:High Court|District Court|Court) +of +(?P<location>[A-Z][A-Za-z]+(?: +[A-Z][A-Za-z]+){0,3})\b"
    )
    known_location_pattern = re.compile(r"\b(?:New Delhi|Delhi|Mumbai|Bengaluru|Bangalore|Chennai|Kolkata|Hyderabad|Pune)\b")
    case_number_pattern = re.compile(
        r"(?i)\b(?:Civil|Criminal)\s+Appeal\s+No\.?\s*[:\-]?\s*[A-Za-z0-9./-]+|(?:Case|Writ Petition|Revision Petition)\s*No\.?\s*[:\-]?\s*[A-Za-z0-9./-]+"
    )
    date_pattern = re.compile(
        r"(?i)\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})\b"
    )
    money_pattern = re.compile(r"(?:₹\s?\d[\d,]*(?:\.\d{1,2})?|Rs\.?\s?\d[\d,]*(?:\.\d{1,2})?|\$\s?\d[\d,]*(?:\.\d{1,2})?)")
    punctuation_cleanup_pattern = re.compile(r"[^\w\s.'&/-]+")
    invalid_party_phrases = {"supersedes", "agreement", "discussion", "discussions", "clause", "section", "parties"}
    organization_markers = {"ltd", "limited", "llp", "inc", "corp", "company", "co", "association", "trust", "bank"}
    role_priority = {
        "first party": 0,
        "second party": 1,
        "partner a": 2,
        "partner b": 3,
        "petitioner": 4,
        "respondent": 5,
        "plaintiff": 6,
        "defendant": 7,
        "party 1": 8,
        "party 2": 9,
    }

    def extract(self, text: str) -> dict:
        doc = spacy_service.get_model()(text)
        persons = self._unique_strings([ent.text for ent in doc.ents if ent.label_ == "PERSON"])
        organizations = self._unique_strings([ent.text for ent in doc.ents if ent.label_ == "ORG"])
        ner_locations = self._unique_locations([ent.text for ent in doc.ents if ent.label_ in {"GPE", "LOC"}])

        parties = self._extract_parties(text, persons, organizations)
        judges = self._unique_strings(self.judge_pattern.findall(text))
        locations = self._unique_locations(
            self.location_at_pattern.findall(text)
            + self.court_location_pattern.findall(text)
            + self.known_location_pattern.findall(text)
            + ner_locations
        )
        case_numbers = self._unique_values(self.case_number_pattern.findall(text))
        dates = self._unique_values(self.date_pattern.findall(text))
        money = self._unique_values(self.money_pattern.findall(text))

        return {
            "judges": judges,
            "parties": parties,
            "locations": locations,
            "dates": dates,
            "case_numbers": case_numbers,
            "money": money,
            "monetary_values": money,
        }

    def _extract_parties(self, text: str, persons: list[str], organizations: list[str]) -> list[dict]:
        parties: list[dict] = []

        for match in self.numbered_party_pattern.finditer(text):
            parties.append(self._build_party(match.group("name"), f"Party {len(parties) + 1}"))

        for pattern in (self.party_designation_pattern, self.party_designation_label_pattern):
            for match in pattern.finditer(text):
                parties.append(self._build_party(match.group("name"), match.group("role")))

        for match in self.party_block_pattern.finditer(text):
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

        unique_parties = self._unique_parties(parties)
        if unique_parties:
            return unique_parties[:4]

        fallback_parties = [
            self._build_party(name, f"Party {index}")
            for index, name in enumerate(persons[:2] + organizations[:2], start=1)
        ]
        return self._unique_parties(fallback_parties)[:4]

    def _build_party(self, raw_name: str, raw_role: str) -> dict:
        name = self._normalize_name(raw_name)
        role = self._normalize_role(raw_role)
        if not self._is_plausible_party_name(name):
            return {"name": "", "role": role}
        return {"name": name, "role": role}

    def _normalize_name(self, value: str) -> str:
        cleaned = self.punctuation_cleanup_pattern.sub(" ", str(value))
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;-/")
        if not cleaned:
            return ""

        tokens: list[str] = []
        for token in cleaned.split():
            lower_token = token.casefold().strip(".")
            if lower_token == "llp":
                tokens.append("LLP")
            elif lower_token == "ltd":
                tokens.append("Ltd.")
            elif lower_token == "pvt":
                tokens.append("Pvt.")
            elif token.isupper() and len(token) > 1:
                tokens.append(token)
            else:
                tokens.append(token.capitalize())
        return " ".join(tokens[:6]).strip()

    def _normalize_role(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" .,:;-/")
        if not cleaned:
            return "Party"
        return " ".join(token.capitalize() for token in cleaned.split())

    def _unique_parties(self, parties: list[dict]) -> list[dict]:
        specific_roles = {
            self._normalize_name(party["name"]).casefold()
            for party in parties
            if party.get("name") and not str(party.get("role", "")).lower().startswith("party ")
        }

        seen: set[tuple[str, str]] = set()
        unique_values: list[dict] = []
        for party in parties:
            name = self._normalize_name(party.get("name", ""))
            role = self._normalize_role(party.get("role", ""))
            if not self._is_plausible_party_name(name):
                continue
            if role.lower().startswith("party ") and name.casefold() in specific_roles:
                continue
            key = (name.casefold(), role.casefold())
            if key in seen:
                continue
            seen.add(key)
            unique_values.append({"name": name, "role": role})

        return sorted(unique_values, key=lambda item: (self.role_priority.get(item["role"].casefold(), 99), item["name"].casefold()))

    def _unique_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []

        for value in values:
            normalized = self._normalize_name(value)
            if not normalized:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
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
            if key in seen:
                continue
            seen.add(key)
            unique_values.append(normalized)

        return unique_values

    def _unique_locations(self, values: list[str]) -> list[str]:
        return self._unique_values([" ".join(token.capitalize() for token in str(value).split()) for value in values if value])

    def _is_plausible_party_name(self, value: str) -> bool:
        if not value:
            return False
        lowered = value.casefold()
        if any(phrase in lowered for phrase in self.invalid_party_phrases):
            return False

        tokens = [token.casefold().strip(".,") for token in value.split() if token]
        if len(tokens) < 2 or len(tokens) > 6:
            return False

        if any(token in self.organization_markers for token in tokens):
            return True

        alpha_tokens = [token for token in tokens if any(char.isalpha() for char in token)]
        return len(alpha_tokens) >= 2


entity_engine = EntityEngine()
