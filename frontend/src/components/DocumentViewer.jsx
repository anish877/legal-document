function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function buildHighlights(text, insights) {
  if (!text) {
    return [{ type: "text", value: "" }];
  }

  const candidates = [
    ...(insights?.locations || []),
    ...(insights?.financial_terms || []),
    ...(insights?.parties_inferred || []),
    ...(insights?.important_clauses || []),
  ]
    .map((item) => item?.trim())
    .filter(Boolean)
    .sort((left, right) => right.length - left.length)
    .slice(0, 20);

  if (!candidates.length) {
    return [{ type: "text", value: text }];
  }

  const matcher = new RegExp(`(${candidates.map(escapeRegExp).join("|")})`, "gi");
  return text.split(matcher).filter(Boolean).map((segment) => {
    const highlighted = candidates.some((candidate) => candidate.toLowerCase() === segment.toLowerCase());
    return { type: highlighted ? "highlight" : "text", value: segment };
  });
}

function MetricPill({ label, value }) {
  return (
    <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600 shadow-sm">
      {label}: {value}
    </span>
  );
}

function MetadataStrip({ metadata, metrics }) {
  const items = [
    metadata?.file_type ? metadata.file_type.toUpperCase() : "PDF",
    metadata?.text_length ? `${metadata.text_length.toLocaleString()} chars` : "Character count pending",
    metadata?.chunk_count ? `${metadata.chunk_count} chunks` : "Chunk count pending",
  ];

  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {items.map((item) => <MetricPill key={item} label="Meta" value={item} />)}
      {metrics?.durations?.parse ? <MetricPill label="Parse" value={`${metrics.durations.parse.toFixed(2)}s`} /> : null}
      {metrics?.durations?.ocr ? <MetricPill label="OCR" value={`${metrics.durations.ocr.toFixed(2)}s`} /> : null}
      {metrics?.durations?.summarize ? <MetricPill label="Summary" value={`${metrics.durations.summarize.toFixed(2)}s`} /> : null}
    </div>
  );
}

export default function DocumentViewer({ text, metadata, insights, metrics }) {
  const segments = buildHighlights(text, insights);

  return (
    <section className="h-full rounded-[30px] border border-[var(--surface-stroke)] bg-[var(--surface)] p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)] backdrop-blur">
      <div className="mb-5">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">Document Viewer</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Read with AI-guided context</h2>
        <p className="mt-2 text-sm leading-7 text-slate-600">
          Highlights are grounded in parties, money, locations, and clause themes extracted from the final result.
        </p>
      </div>

      <MetadataStrip metadata={metadata} metrics={metrics} />

      <div className="h-[760px] overflow-y-auto rounded-[24px] border border-slate-200 bg-[#f8fafc] p-6">
        {text ? (
          <pre className="font-jetbrains whitespace-pre-wrap text-sm leading-[1.7] text-slate-800">
            {segments.map((segment, index) =>
              segment.type === "highlight" ? (
                <mark
                  key={`${segment.value}-${index}`}
                  className="rounded-md bg-amber-100 px-1 py-0.5 text-slate-950 shadow-[inset_0_0_0_1px_rgba(245,158,11,0.15)]"
                >
                  {segment.value}
                </mark>
              ) : (
                <span key={`${segment.value}-${index}`}>{segment.value}</span>
              ),
            )}
          </pre>
        ) : (
          <div className="flex h-full items-center justify-center text-center text-sm text-slate-500">
            Upload a document to start the live analysis workflow.
          </div>
        )}
      </div>
    </section>
  );
}
