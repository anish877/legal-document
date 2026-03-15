import ClauseCard from "./ClauseCard";
import VerdictBanner from "./VerdictBanner";
import SummaryCard from "./SummaryCard";
import KeyInfoPanel from "./KeyInfoPanel";

function OverviewCard({ insights }) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-gradient-to-br from-blue-600 to-slate-950 p-5 text-white shadow-sm transition hover:shadow-md">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-blue-100">Document Type</p>
      <h2 className="mt-3 text-2xl font-semibold">{insights?.document_type || "Legal Document"}</h2>
      <p className="mt-3 text-sm leading-7 text-blue-50">
        The analysis panel stays useful even when strict extraction is sparse by leaning on summary-derived
        structured insights.
      </p>
    </section>
  );
}

function MetricsCard({ metrics }) {
  const durations = metrics?.durations || {};
  const items = [
    ["Parse", durations.parse],
    ["OCR", durations.ocr],
    ["Summary", durations.summarize],
    ["Entities", durations.entities],
    ["Clauses", durations.clauses],
  ].filter(([, value]) => typeof value === "number");

  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">Backend Timings</p>
      <div className="mt-4 grid grid-cols-2 gap-3">
        {items.length ? (
          items.map(([label, value]) => (
            <div key={label} className="rounded-2xl bg-slate-50 px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{value.toFixed(2)}s</p>
            </div>
          ))
        ) : (
          <div className="col-span-2 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
            Timings appear after analysis completes.
          </div>
        )}
      </div>
    </section>
  );
}

function RisksCard({ risks = [] }) {
  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-rose-500">Risk Signals</p>
      <div className="mt-4 space-y-3">
        {risks.length ? (
          risks.map((risk) => (
            <article key={`${risk.title}-${risk.level}`} className="rounded-2xl border border-rose-100 bg-rose-50/60 p-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-900">{risk.title}</h3>
                <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-rose-700">
                  {risk.level}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-700">{risk.description}</p>
              <p className="mt-2 text-sm font-medium text-slate-900">{risk.recommendation}</p>
            </article>
          ))
        ) : (
          <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">No explicit risk flags yet.</div>
        )}
      </div>
    </section>
  );
}

function ClauseGrid({ clauses }) {
  const clauseEntries = clauses
    ? [
        ["Payment", clauses.payment_clause],
        ["Confidentiality", clauses.confidentiality_clause],
        ["Termination", clauses.termination_clause],
        ["Governing Law", clauses.governing_law_clause],
      ]
    : [];

  return (
    <section className="rounded-[24px] border border-slate-200/80 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">Clause Coverage</p>
      <div className="mt-4 grid gap-3">
        {clauseEntries.length ? (
          clauseEntries.map(([title, detail]) => <ClauseCard key={title} title={title} detail={detail} />)
        ) : (
          <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">Clause analysis will appear here.</div>
        )}
      </div>
    </section>
  );
}

export default function AnalysisPanel({ result }) {
  return (
    <aside className="flex h-full flex-col gap-4">
      <OverviewCard insights={result?.insights} />
      <VerdictBanner verdict={result?.verdict} />
      <SummaryCard summary={result?.summary} detailedSummary={result?.detailed_summary} />
      <KeyInfoPanel insights={result?.insights} />
      <ClauseGrid clauses={result?.clauses} />
      <RisksCard risks={result?.risks} />
      <MetricsCard metrics={result?.debug?.metrics} />
    </aside>
  );
}
