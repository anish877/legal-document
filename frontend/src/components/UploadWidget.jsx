export default function UploadWidget({ file, busy, status, error }) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-500">Workspace Status</p>
          <h2 className="mt-2 text-lg font-semibold text-slate-900">
            {file ? file.name : "Upload a legal PDF or text file to begin"}
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {status?.description || "The analyzer will extract text, build AI summaries, and surface key legal signals."}
          </p>
        </div>

        <div className="min-w-[220px] rounded-2xl bg-slate-950 px-4 py-4 text-sm text-white shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">Current State</p>
          <p className="mt-2 text-lg font-semibold">{status?.title || "Awaiting document"}</p>
          <p className="mt-2 text-slate-300">{busy ? "AI analysis is in motion." : "Ready when you are."}</p>
          {error ? <p className="mt-3 text-rose-300">{error}</p> : null}
        </div>
      </div>
    </section>
  );
}
