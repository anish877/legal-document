const STEPS = [
  { key: "upload", label: "File Intake", stages: ["upload"] },
  { key: "extract", label: "Text Extraction", stages: ["extract"] },
  { key: "analysis", label: "Legal Analysis", stages: ["normalize", "summarize", "entities", "clauses", "verdict", "risks", "analyze"] },
  { key: "complete", label: "Ready", stages: ["complete"] },
];

function isStepComplete(step, stage, completed) {
  if (completed) return true;
  if (step.key === "upload") return stage !== "idle";
  if (step.key === "extract") return !["idle", "upload", "extract"].includes(stage);
  if (step.key === "analysis") return ["complete", "error"].includes(stage);
  return false;
}

function isStepCurrent(step, stage, busy, completed) {
  if (!busy || completed) return false;
  return step.stages.includes(stage) || (step.key === "analysis" && ["summarize", "entities", "clauses", "verdict", "risks"].includes(stage));
}

export default function ProgressIndicator({ busy, completed, progress = 0, stage = "idle", events = [] }) {
  return (
    <section className="rounded-[28px] border border-[var(--surface-stroke)] bg-[var(--surface)] p-5 shadow-sm backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <p className="section-title">Analysis Progress</p>
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          {busy ? "Streaming live" : completed ? "Ready" : "Waiting"}
        </span>
      </div>

      <div className="mb-5 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,var(--brand-strong),var(--accent))] transition-all duration-500"
          style={{ width: `${Math.max(4, Math.round(progress * 100))}%` }}
        />
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        {STEPS.map((step, index) => {
          const complete = isStepComplete(step, stage, completed);
          const current = isStepCurrent(step, stage, busy, completed);
          return (
            <div
              key={step.key}
              className={`relative overflow-hidden rounded-2xl border px-4 py-4 transition ${
                current
                  ? "border-blue-200 bg-blue-50 shadow-sm"
                  : complete
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-slate-200 bg-slate-50"
              }`}
            >
              {current ? (
                <div className="absolute inset-0 bg-[linear-gradient(110deg,transparent,rgba(37,99,235,0.12),transparent)] animate-pulse" />
              ) : null}
              <div className="flex items-center gap-3">
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                    complete
                      ? "bg-emerald-500 text-white"
                    : current
                        ? "bg-blue-600 text-white"
                        : "bg-slate-200 text-slate-600"
                  }`}
                >
                  {complete ? "✓" : index + 1}
                </span>
                <div>
                  <div className="text-sm font-semibold text-slate-800">{step.label}</div>
                  <div className="text-xs text-slate-500">
                    {completed ? "Completed" : current ? "Running" : complete ? "Completed" : "Pending"}
                  </div>
                </div>
              </div>
              {index < STEPS.length - 1 ? (
                <div className="pointer-events-none absolute -right-2 top-1/2 hidden h-px w-4 bg-slate-300 md:block" />
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {events.slice(0, 3).map((event) => (
          <div key={event.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{event.stage}</p>
            <p className="mt-2 text-sm text-slate-700">{event.message}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
