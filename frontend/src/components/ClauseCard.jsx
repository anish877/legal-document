function getClauseState(detail) {
  const confidence = detail?.confidence || 0;
  if (detail?.present && confidence >= 0.7) {
    return {
      label: "Present",
      dot: "bg-emerald-500",
      badge: "bg-emerald-50 text-emerald-700",
      border: "border-emerald-200",
    };
  }
  if (detail?.present || confidence >= 0.4) {
    return {
      label: "Uncertain",
      dot: "bg-amber-400",
      badge: "bg-amber-50 text-amber-700",
      border: "border-amber-200",
    };
  }
  return {
    label: "Missing",
    dot: "bg-rose-500",
    badge: "bg-rose-50 text-rose-700",
    border: "border-rose-200",
  };
}

export default function ClauseCard({ title, detail }) {
  const state = getClauseState(detail);

  return (
    <article className={`rounded-xl border bg-white p-4 shadow-sm ${state.border}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
          <div className="mt-3 flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${state.dot}`} />
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${state.badge}`}>
              {state.label}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Confidence</div>
          <div className="mt-1 text-sm font-semibold text-slate-800">
            {Math.round((detail?.confidence || 0) * 100)}%
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {detail?.text ? (
          <div className="rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700">{detail.text}</div>
        ) : detail?.evidence?.length ? (
          detail.evidence.map((item) => (
            <div key={item} className="rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700">
              {item}
            </div>
          ))
        ) : (
          <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">No direct evidence captured.</div>
        )}
      </div>
    </article>
  );
}
