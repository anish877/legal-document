export default function PartyCard({ party }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{party.label}</p>
          <h4 className="mt-2 text-base font-semibold text-slate-900">{party.name}</h4>
        </div>
        <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
          {Math.round((party.confidence || 0) * 100)}%
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm text-slate-700">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Role</dt>
          <dd className="mt-1">{party.role}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Designation</dt>
          <dd className="mt-1">{party.designation}</dd>
        </div>
      </dl>
    </article>
  );
}
