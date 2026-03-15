function StatPill({ value }) {
  return (
    <span className="rounded-full border border-[var(--surface-stroke)] bg-white/85 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm backdrop-blur">
      {value}
    </span>
  );
}

function stateLabel(connectionState) {
  if (connectionState === "streaming") return "SSE live";
  if (connectionState === "connecting") return "Connecting";
  if (connectionState === "error") return "Stream issue";
  if (connectionState === "closed") return "Completed";
  return "Idle";
}

export default function HeaderBar({ file, metadata, metrics, jobId, connectionState, onFileSelect, onAnalyze, busy }) {
  const stats = [
    metadata?.pages ? `${metadata.pages} pages` : "Pages pending",
    metadata?.text_length ? `${metadata.text_length.toLocaleString()} chars` : "Words pending",
    metadata?.chunk_count ? `${metadata.chunk_count} chunks` : "Chunks pending",
    metrics?.durations?.summarize ? `${metrics.durations.summarize.toFixed(2)}s summary` : stateLabel(connectionState),
  ];

  return (
    <header className="rounded-[32px] border border-[var(--surface-stroke)] bg-[var(--surface)] px-6 py-6 shadow-[0_24px_70px_rgba(15,23,42,0.10)] backdrop-blur">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--brand-strong)]">Live Analysis Workspace</p>
          <h1 className="mt-2 font-display text-3xl text-slate-950 md:text-5xl">Legal AI Analyzer</h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            Upload a contract, petition, or judgment and watch the backend move through extraction, clause checks,
            risk scoring, and summary generation in real time.
          </p>
        </div>

        <div className="flex flex-col gap-4 xl:items-end">
          <div className="flex flex-wrap gap-2">
            {stats.map((stat) => (
              <StatPill key={stat} value={stat} />
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <label className="inline-flex cursor-pointer items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
              Upload Document
              <input
                className="hidden"
                type="file"
                accept=".pdf,.txt,text/plain,application/pdf"
                onChange={(event) => onFileSelect(event.target.files?.[0] || null)}
              />
            </label>

            <button
              type="button"
              disabled={!file || busy}
              onClick={onAnalyze}
              className="inline-flex items-center justify-center rounded-xl bg-[var(--brand-strong)] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-[var(--brand)] hover:shadow-md disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {busy ? "Streaming Analysis..." : "Start Live Analysis"}
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            <span className="rounded-full bg-slate-950 px-3 py-1.5 text-white">{stateLabel(connectionState)}</span>
            {jobId ? <span className="rounded-full bg-white px-3 py-1.5 shadow-sm">Job {jobId.slice(0, 8)}</span> : null}
          </div>
        </div>
      </div>
    </header>
  );
}
