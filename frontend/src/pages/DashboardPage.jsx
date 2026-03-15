import { startTransition, useEffect, useRef, useState } from "react";

import AnalysisPanel from "../components/AnalysisPanel";
import DocumentViewer from "../components/DocumentViewer";
import HeaderBar from "../components/HeaderBar";
import ProgressIndicator from "../components/ProgressIndicator";
import UploadWidget from "../components/UploadWidget";
import { startAnalysisJob, subscribeToAnalysisJob } from "../api/client";

const defaultStatus = {
  title: "Awaiting document",
  description: "Select a file to begin extraction and AI analysis.",
  progress: 0,
  stage: "idle",
};

export default function DashboardPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState(defaultStatus);
  const [liveEvents, setLiveEvents] = useState([]);
  const [jobId, setJobId] = useState("");
  const [connectionState, setConnectionState] = useState("idle");
  const eventSourceRef = useRef(null);

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  function pushEvent(nextEvent) {
    setLiveEvents((existing) => [nextEvent, ...existing].slice(0, 8));
  }

  function updateFromPayload(type, payload) {
    const stage = payload.stage || (type.startsWith("job.") ? type.replace("job.", "") : "analyze");
    const title = type === "job.completed" ? "Analysis complete" : type === "job.failed" ? "Analysis failed" : "Live backend analysis";
    const nextStatus = {
      title,
      description: payload.message || "The backend is processing your document.",
      progress: payload.progress || 0,
      stage,
    };

    startTransition(() => {
      setStatus(nextStatus);
      pushEvent({
        id: `${type}-${payload.updated_at || payload.progress || Math.random()}`,
        type,
        stage,
        message: payload.message,
        progress: payload.progress || 0,
        detail: payload.detail || {},
        updatedAt: payload.updated_at || new Date().toISOString(),
      });
    });
  }

  async function handleAnalyze() {
    if (!selectedFile) {
      return;
    }

    eventSourceRef.current?.close();
    setBusy(true);
    setError("");
    setResult(null);
    setLiveEvents([]);
    setJobId("");
    setConnectionState("connecting");
    setStatus({
      title: "Starting live analysis",
      description: "Uploading the document and preparing a live backend event stream.",
      progress: 0.02,
      stage: "upload",
    });

    try {
      const job = await startAnalysisJob(selectedFile);
      setJobId(job.job_id);
      setConnectionState("streaming");

      eventSourceRef.current = subscribeToAnalysisJob(job.job_id, {
        onEvent: ({ type, payload }) => {
          updateFromPayload(type, payload);
        },
        onComplete: (payload) => {
          setConnectionState("closed");
          setBusy(false);
          setResult(payload.result);
          updateFromPayload("job.completed", payload);
        },
        onError: (streamError) => {
          setConnectionState("error");
          setBusy(false);
          setError(streamError.message || "Unable to stream analysis progress.");
          setStatus({
            title: "Analysis failed",
            description: streamError.message || "Check the backend server and retry.",
            progress: status.progress || 0,
            stage: "error",
          });
        },
      });
    } catch (requestError) {
      setError(requestError.message || "Unable to analyze the document.");
      setConnectionState("error");
      setStatus({
        title: "Analysis failed",
        description: "The backend could not start the analysis job.",
        progress: 0,
        stage: "error",
      });
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[var(--app-bg)] px-4 py-6 text-slate-900 md:px-6 xl:px-8">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-6">
        <HeaderBar
          file={selectedFile}
          metadata={result?.metadata}
          metrics={result?.debug?.metrics}
          jobId={jobId}
          connectionState={connectionState}
          onFileSelect={setSelectedFile}
          onAnalyze={handleAnalyze}
          busy={busy}
        />

        <UploadWidget
          file={selectedFile}
          status={status}
          busy={busy}
          error={error}
          connectionState={connectionState}
          events={liveEvents}
        />

        <ProgressIndicator
          busy={busy}
          completed={Boolean(result)}
          progress={status.progress}
          stage={status.stage}
          events={liveEvents}
        />

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,0.75fr)]">
          <DocumentViewer
            text={result?.extracted_text}
            metadata={result?.metadata}
            insights={result?.insights}
            metrics={result?.debug?.metrics}
          />
          <AnalysisPanel result={result} />
        </section>
      </div>
    </main>
  );
}
