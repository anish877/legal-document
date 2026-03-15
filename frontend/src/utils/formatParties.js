const ROLE_PATTERNS = [
  { pattern: /\b(first party|party 1)\b/i, designation: "First Party" },
  { pattern: /\b(second party|party 2)\b/i, designation: "Second Party" },
  { pattern: /\bthird party|party 3\b/i, designation: "Third Party" },
  { pattern: /\bpetitioner\b/i, designation: "Petitioner" },
  { pattern: /\brespondent\b/i, designation: "Respondent" },
  { pattern: /\bplaintiff\b/i, designation: "Plaintiff" },
  { pattern: /\bdefendant\b/i, designation: "Defendant" },
  { pattern: /\bhusband\b/i, designation: "Husband" },
  { pattern: /\bwife\b/i, designation: "Wife" },
  { pattern: /\bappellant\b/i, designation: "Appellant" },
  { pattern: /\bclaimant\b/i, designation: "Claimant" },
];

function cleanTokens(value) {
  return String(value || "")
    .replace(/#/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function extractName(raw) {
  const cleaned = cleanTokens(raw);
  const withoutRoleWords = cleaned
    .replace(
      /\b(first party|second party|third party|party 1|party 2|party 3|wife|husband|petitioner|respondent|plaintiff|defendant|appellant|claimant)\b/gi,
      " ",
    )
    .replace(/\s+/g, " ")
    .trim();

  const titleCaseName = withoutRoleWords
    .split(" ")
    .filter((token) => token && /^[A-Za-z.'-]+$/.test(token))
    .slice(0, 4)
    .join(" ");

  return titleCaseName || cleaned;
}

function extractRoleMetadata(raw) {
  const designations = ROLE_PATTERNS.filter(({ pattern }) => pattern.test(raw)).map(
    ({ designation }) => designation,
  );

  const role = designations.filter((item) => !item.toLowerCase().includes("party")).join(" / ") || "Party";
  const designation = designations.find((item) => item.toLowerCase().includes("party")) || "Unspecified";

  return { role, designation };
}

export function formatParties(entities, insights) {
  const parties = entities?.parties?.length
    ? entities.parties
    : (insights?.parties_inferred || []).map((name) => ({ name, role: "AI Inferred Party" }));

  return parties.map((party, index) => {
    const rawValue = typeof party === "string" ? party : `${party?.name || ""} ${party?.role || ""}`.trim();
    const explicitRole = typeof party === "object" ? cleanTokens(party?.role) : "";
    const { role, designation } = extractRoleMetadata(rawValue);
    const resolvedRole = explicitRole || role;
    const resolvedName = typeof party === "object" ? cleanTokens(party?.name) || extractName(rawValue) : extractName(rawValue);
    const resolvedDesignation = designation !== "Unspecified" ? designation : explicitRole || designation;

    return {
      id: `${resolvedName}-${index}`,
      label: `Party ${index + 1}`,
      name: resolvedName,
      role: resolvedRole || "Party",
      designation: resolvedDesignation === "Unspecified" ? "AI inferred" : resolvedDesignation,
      raw: rawValue,
      confidence: entities?.parties?.length ? 0.82 : 0.68,
    };
  });
}
