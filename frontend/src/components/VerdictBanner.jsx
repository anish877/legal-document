export default function VerdictBanner({ verdict }) {
  return (
    <section className="rounded-2xl bg-gradient-to-r from-slate-900 to-slate-700 p-5 text-white shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-300">Verdict Detection</p>
      <p className="mt-3 font-display text-3xl">{verdict || "Awaiting analysis"}</p>
      <p className="mt-2 text-sm text-slate-200">
        Final disposition is inferred from the concluding sections of the extracted document.
      </p>
    </section>
  );
}
