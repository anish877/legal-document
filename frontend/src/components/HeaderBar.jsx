function StatPill({ value }) {
  return (
    <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs font-semibold text-slate-600 shadow-sm backdrop-blur">
      {value}
    </span>
  );
}

export default function HeaderBar({ file, metadata, onFileSelect, onAnalyze, busy }) {
  const stats = [
    metadata?.pages ? `${metadata.pages} pages` : "Pages pending",
    metadata?.text_length ? `${metadata.text_length.toLocaleString()} chars` : "Words pending",
    metadata?.chunk_count ? `${metadata.chunk_count} chunks` : "Chunks pending",
  ];

  return (
    <header className="rounded-[28px] border border-slate-200/80 bg-white/90 px-6 py-5 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-blue-600">AI Workspace</p>
          <h1 className="mt-2 font-display text-3xl text-slate-950 md:text-4xl">Legal AI Analyzer</h1>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
            Review dense legal documents in a cleaner workspace with AI summaries, inferred key facts, and
            guided reading.
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
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-md disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {busy ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
