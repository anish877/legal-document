import TagList from "./TagList";

export default function KeyInfoPanel({ insights }) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="mb-5">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-amber-500">Key Information</p>
        <h2 className="mt-2 text-xl font-semibold text-slate-950">Structured facts surfaced by AI</h2>
      </div>

      <div className="space-y-5">
        <TagList
          title="Parties"
          items={insights?.parties_inferred || []}
          tone="blue"
          emptyLabel="No parties inferred"
        />
        <TagList
          title="Locations"
          items={insights?.locations || []}
          tone="emerald"
          emptyLabel="No locations inferred"
        />
        <TagList
          title="Financial Terms"
          items={insights?.financial_terms || []}
          tone="amber"
          emptyLabel="No financial terms inferred"
        />
        <TagList
          title="Important Clauses"
          items={insights?.important_clauses || []}
          tone="slate"
          emptyLabel="No clauses inferred"
        />
      </div>
    </section>
  );
}
