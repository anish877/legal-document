import { useEffect, useState } from "react";

import AnalysisPanel from "../components/AnalysisPanel";
import DocumentViewer from "../components/DocumentViewer";
import HeaderBar from "../components/HeaderBar";
import ProgressIndicator from "../components/ProgressIndicator";
import UploadWidget from "../components/UploadWidget";
import { uploadDocument } from "../api/client";

const defaultStatus = {
  title: "Awaiting document",
  description: "Select a file to begin extraction and AI analysis.",
};

export default function DashboardPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [status, setStatus] = useState(defaultStatus);

  useEffect(() => {
    if (!busy) {
      setCurrentStep(0);
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setCurrentStep((step) => (step + 1) % 4);
    }, 1100);

    return () => window.clearInterval(intervalId);
  }, [busy]);

  async function handleAnalyze() {
    if (!selectedFile) {
      return;
    }

    setBusy(true);
    setCurrentStep(0);
    setError("");
    setStatus({
      title: "Backend analysis running",
      description: "Uploading the document, extracting text, and generating AI summary insights.",
    });

    try {
      const payload = await uploadDocument(selectedFile);
      setResult(payload);
      setStatus({
        title: "Analysis complete",
        description: "Structured insights are available in the review panel.",
      });
    } catch (requestError) {
      setError(requestError.message || "Unable to analyze the document.");
      setStatus({
        title: "Analysis failed",
        description: "Check the backend server, model dependencies, or OCR configuration.",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f8fafc] px-4 py-6 text-slate-900 md:px-6 xl:px-8">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-6">
        <HeaderBar
          file={selectedFile}
          metadata={result?.metadata}
          onFileSelect={setSelectedFile}
          onAnalyze={handleAnalyze}
          busy={busy}
        />

        <UploadWidget file={selectedFile} status={status} busy={busy} error={error} />

        <ProgressIndicator busy={busy} completed={Boolean(result)} currentStep={currentStep} />

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.75fr)]">
          <DocumentViewer text={result?.extracted_text} metadata={result?.metadata} insights={result?.insights} />
          <AnalysisPanel result={result} />
        </section>
      </div>
    </main>
  );
}
