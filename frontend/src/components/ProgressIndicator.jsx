const STEPS = ["Uploading", "Extracting text", "Analyzing document", "Generating summary"];

export default function ProgressIndicator({ busy, completed, currentStep = 0 }) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white/80 p-5 shadow-sm backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <p className="section-title">Analysis Progress</p>
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          {busy ? "In progress" : completed ? "Ready" : "Waiting"}
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        {STEPS.map((step, index) => {
          const complete = completed || (busy && index < currentStep);
          const current = busy && index === currentStep;
          return (
            <div
              key={step}
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
                  {index + 1}
                </span>
                <div>
                  <div className="text-sm font-semibold text-slate-800">{step}</div>
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
    </section>
  );
}
