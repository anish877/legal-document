function EventRow({ event }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200">{event.stage || "Update"}</p>
        <p className="mt-1 text-sm text-white">{event.message}</p>
      </div>
      <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold text-white/85">
        {Math.round((event.progress || 0) * 100)}%
      </span>
    </div>
  );
}

export default function UploadWidget({ file, busy, status, error, connectionState, events = [] }) {
  return (
    <section className="rounded-[28px] border border-[var(--surface-stroke)] bg-[linear-gradient(135deg,#0f172a_0%,#12324a_45%,#174a57_100%)] p-5 text-white shadow-[0_20px_50px_rgba(15,23,42,0.18)]">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(300px,0.9fr)]">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-200">Workspace Status</p>
          <h2 className="mt-2 text-xl font-semibold text-white">
            {file ? file.name : "Upload a legal PDF or text file to begin"}
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-200">
            {status?.description || "The analyzer will extract text, build AI summaries, and surface key legal signals."}
          </p>
          <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-[linear-gradient(90deg,#34d399_0%,#fbbf24_50%,#f97316_100%)] transition-all duration-500"
              style={{ width: `${Math.max(4, Math.round((status?.progress || 0) * 100))}%` }}
            />
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.2em]">
            <span className="rounded-full bg-white/10 px-3 py-1.5 text-white/90">{status?.stage || "idle"}</span>
            <span className="rounded-full bg-white/10 px-3 py-1.5 text-white/90">{connectionState || "idle"}</span>
            <span className="rounded-full bg-white/10 px-3 py-1.5 text-white/90">
              {Math.round((status?.progress || 0) * 100)}% complete
            </span>
          </div>
          {error ? <p className="mt-4 text-sm text-rose-200">{error}</p> : null}
        </div>

        <div className="min-w-[220px] rounded-[24px] border border-white/10 bg-black/15 px-4 py-4 text-sm text-white backdrop-blur">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-300">Live Feed</p>
            <p className="text-xs text-slate-300">{busy ? "Backend active" : "Waiting"}</p>
          </div>
          <p className="mb-3 text-lg font-semibold">{status?.title || "Awaiting document"}</p>
          <div className="space-y-2">
            {events.length ? (
              events.slice(0, 4).map((event) => <EventRow key={event.id} event={event} />)
            ) : (
              <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-4 text-sm text-slate-200">
                Start an analysis to see real SSE updates from the backend pipeline.
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
