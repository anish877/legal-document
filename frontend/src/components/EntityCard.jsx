export default function EntityCard({ label, value, confidence = 0.78 }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
          <p className="mt-2 text-sm font-medium leading-6 text-slate-800">{value}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
          {Math.round(confidence * 100)}%
        </span>
      </div>
    </article>
  );
}
