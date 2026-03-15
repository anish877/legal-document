const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function handleResponse(response) {
  if (!response.ok) {
    let detail = "Request failed.";
    try {
      const payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  return response.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload-document`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}

export async function startAnalysisJob(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/analysis-jobs`, {
    method: "POST",
    body: formData,
  });

  return handleResponse(response);
}

export function subscribeToAnalysisJob(jobId, { onEvent, onComplete, onError }) {
  const source = new EventSource(`${API_BASE_URL}/analysis-jobs/${jobId}/events`);
  const eventNames = ["job.queued", "job.started", "analysis.progress", "job.completed", "job.failed"];

  eventNames.forEach((eventName) => {
    source.addEventListener(eventName, (event) => {
      const payload = JSON.parse(event.data);
      onEvent?.({ type: eventName, payload });

      if (eventName === "job.completed") {
        onComplete?.(payload);
        source.close();
      }

      if (eventName === "job.failed") {
        onError?.(new Error(payload.error || "Analysis failed."));
        source.close();
      }
    });
  });

  source.onerror = () => {
    onError?.(new Error("The live analysis stream disconnected."));
    source.close();
  };

  return source;
}

export async function summarizeText(text) {
  const response = await fetch(`${API_BASE_URL}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  return handleResponse(response);
}
