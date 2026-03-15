export default function TagList({ title, items, tone = "blue", emptyLabel }) {
  const toneMap = {
    blue: "bg-blue-50 text-blue-700 ring-blue-100",
    amber: "bg-amber-50 text-amber-700 ring-amber-100",
    emerald: "bg-emerald-50 text-emerald-700 ring-emerald-100",
    slate: "bg-slate-100 text-slate-700 ring-slate-200",
  };

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2.5">
        {items?.length ? (
          items.map((item) => (
            <span
              key={`${title}-${item}`}
              className={`rounded-full px-3 py-2 text-sm font-medium ring-1 transition hover:-translate-y-0.5 hover:shadow-sm ${toneMap[tone] || toneMap.blue}`}
            >
              {item}
            </span>
          ))
        ) : (
          <span className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-500 ring-1 ring-slate-200">
            {emptyLabel}
          </span>
        )}
      </div>
    </div>
  );
}
