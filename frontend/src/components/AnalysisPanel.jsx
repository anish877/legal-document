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

export default function AnalysisPanel({ result }) {
  return (
    <aside className="flex h-full flex-col gap-4">
      <OverviewCard insights={result?.insights} />
      <SummaryCard summary={result?.summary} detailedSummary={result?.detailed_summary} />
      <KeyInfoPanel insights={result?.insights} />
    </aside>
  );
}
