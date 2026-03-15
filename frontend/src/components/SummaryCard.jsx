export default function SummaryCard({ summary, detailedSummary }) {
  return (
    <section className="overflow-hidden rounded-[24px] border border-slate-200/80 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-blue-600">AI Summary</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">Document understanding at a glance</h2>
        </div>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">Generated</span>
      </div>

      <p className="mt-4 text-sm leading-7 text-slate-700">
        {summary || "A concise summary will appear here after analysis completes."}
      </p>

      <details className="group mt-5 rounded-2xl bg-slate-50 p-4">
        <summary className="cursor-pointer list-none text-sm font-semibold text-slate-800">
          <span className="group-open:hidden">Detailed Summary</span>
          <span className="hidden group-open:inline">Hide Detailed Summary</span>
        </summary>
        <p className="mt-3 text-sm leading-7 text-slate-700">
          {detailedSummary || "A longer AI-generated summary will appear here after analysis completes."}
        </p>
      </details>
    </section>
  );
}
