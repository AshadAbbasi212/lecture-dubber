"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, Job } from "@/lib/api";
import { 
  Sparkles, 
  Clock, 
  ArrowRight, 
  FileCheck2, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  XCircle, 
  Film, 
  Music, 
  Mic, 
  Languages, 
  Layers, 
  SlidersHorizontal,
  Download
} from "lucide-react";

const STAGES = [
  { id: "ingesting", label: "Ingest", icon: Film },
  { id: "extracting", label: "Extract Audio", icon: Music },
  { id: "separating", label: "Stem Separation", icon: Music },
  { id: "transcribing", label: "ASR Transcription", icon: Mic },
  { id: "translating", label: "Translation", icon: Languages },
  { id: "synthesizing", label: "Voice Synthesis", icon: Mic },
  { id: "mixing", label: "Timeline Mixing", icon: SlidersHorizontal },
  { id: "muxing", label: "Video Muxing", icon: Film },
];

interface JobDetailPageProps {
  params: Promise<{ id: string }>;
}

function JobDetailContent({ params }: JobDetailPageProps) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const router = useRouter();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [canceling, setCanceling] = useState(false);

  const fetchJob = async () => {
    try {
      const data = await api.getJob(jobId);
      setJob(data);
    } catch (err) {
      console.error("Failed to load job details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJob();

    // SSE progress listener
    const token = api.getToken();
    const sseUrl = `http://localhost:8000/api/jobs/${jobId}/events${token ? `?auth_token=${token}` : ""}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.addEventListener("progress", (e) => {
      try {
        const update = JSON.parse(e.data);
        setJob((prev) => prev ? { ...prev, ...update } : null);
      } catch (err) {
        console.error("SSE parse error", err);
      }
    });

    const pollInterval = setInterval(fetchJob, 5000);

    return () => {
      eventSource.close();
      clearInterval(pollInterval);
    };
  }, [jobId]);

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel this dubbing job?")) return;
    setCanceling(true);
    try {
      const updated = await api.cancelJob(jobId);
      setJob(updated);
    } catch (err: any) {
      alert("Failed to cancel job: " + err.message);
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24 text-slate-400 gap-3">
        <span className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>
        Loading job status...
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex-1 flex items-center justify-center py-24 text-center">
        <div className="glass-panel p-8 rounded-2xl max-w-md space-y-4">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Job Not Found</h2>
          <p className="text-xs text-slate-400">This job may have been deleted or expired.</p>
          <Link href="/dashboard" className="inline-block px-4 py-2 bg-indigo-600 rounded-xl text-sm font-medium text-white">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const currentStageIdx = STAGES.findIndex((s) => s.id === job.stage);

  return (
    <div className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-1">
            Job ID: {job.id}
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <span className="truncate max-w-md">{job.source_ref}</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
              {job.source_lang || "en"} → {job.target_lang}
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {job.status === "running" && (
            <button
              onClick={handleCancel}
              disabled={canceling}
              className="px-3.5 py-2 rounded-xl border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-xs font-medium transition-colors flex items-center gap-1.5"
            >
              <XCircle className="w-4 h-4" />
              Cancel Job
            </button>
          )}

          {job.status === "awaiting_review" && (
            <Link
              href={`/jobs/${job.id}/review`}
              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-sm shadow-lg shadow-amber-500/25 flex items-center gap-2 animate-pulse transition-all"
            >
              <FileCheck2 className="w-4 h-4" />
              Review Translations Now
            </Link>
          )}

          {job.status === "completed" && (
            <Link
              href={`/jobs/${job.id}/result`}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/25 flex items-center gap-2 transition-all"
            >
              <Download className="w-4 h-4" />
              View & Download Output
            </Link>
          )}
        </div>
      </div>

      {/* Prominent Callout if Awaiting Review */}
      {job.status === "awaiting_review" && (
        <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-amber-300 flex items-center gap-2">
              <FileCheck2 className="w-5 h-5" />
              Translation Complete — Awaiting Your Approval
            </h3>
            <p className="text-xs text-slate-300">
              Review and edit the translated sentences side-by-side with RTL Urdu support. Once you approve, voice synthesis and tone cloning will begin.
            </p>
          </div>
          <Link
            href={`/jobs/${job.id}/review`}
            className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm shadow-md whitespace-nowrap"
          >
            Open Review Editor →
          </Link>
        </div>
      )}

      {/* Failure Banner */}
      {job.status === "failed" && (
        <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-2">
          <div className="font-semibold flex items-center gap-2 text-rose-200">
            <AlertCircle className="w-5 h-5 text-rose-400" />
            Job Failed During Execution
          </div>
          <p className="text-xs font-mono bg-slate-950/80 p-3 rounded-xl border border-rose-900/50 overflow-x-auto text-rose-400">
            {job.error || "An unknown error occurred during media processing."}
          </p>
        </div>
      )}

      {/* Progress & Estimates Card */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs text-slate-400">Current Pipeline Status</div>
            <div className="text-xl font-bold text-white capitalize flex items-center gap-2 mt-0.5">
              <span>{job.status.replace("_", " ")}</span>
              <span className="text-xs font-mono text-slate-500">• Stage: {job.stage}</span>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {job.estimated_seconds_remaining && job.estimated_seconds_remaining > 0 ? (
              <div className="text-right">
                <div className="text-xs text-slate-400 flex items-center gap-1 justify-end">
                  <Clock className="w-3.5 h-3.5 text-indigo-400" />
                  Estimated Remaining
                </div>
                <div className="text-sm font-semibold text-indigo-300">
                  ~{Math.ceil(job.estimated_seconds_remaining / 60)} minutes
                </div>
              </div>
            ) : null}

            <div className="text-right">
              <div className="text-xs text-slate-400">Overall Progress</div>
              <div className="text-2xl font-black text-white">{job.progress}%</div>
            </div>
          </div>
        </div>

        {/* Big Progress Bar */}
        <div className="w-full h-3 rounded-full bg-slate-900 overflow-hidden border border-slate-800 p-0.5">
          <div
            className={`h-full rounded-full transition-all duration-700 ${
              job.status === "completed"
                ? "bg-emerald-500"
                : job.status === "failed"
                ? "bg-rose-500"
                : job.status === "awaiting_review"
                ? "bg-amber-500"
                : "bg-gradient-to-r from-indigo-500 to-cyan-400"
            }`}
            style={{ width: `${job.progress}%` }}
          />
        </div>

        {/* Visual Pipeline Stages Stepper */}
        <div className="pt-4 border-t border-slate-800/80">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Stage Execution Sequence
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {STAGES.map((s, idx) => {
              const isPast = currentStageIdx > idx || job.status === "completed";
              const isCurrent = currentStageIdx === idx && job.status === "running";
              const isReviewActive = job.status === "awaiting_review" && s.id === "translating";
              const Icon = s.icon;

              return (
                <div
                  key={s.id}
                  className={`p-3 rounded-xl border flex flex-col items-center text-center space-y-1.5 transition-all ${
                    isPast
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : isCurrent
                      ? "bg-indigo-600/20 border-indigo-500/40 text-indigo-300 ring-2 ring-indigo-500/20"
                      : isReviewActive
                      ? "bg-amber-500/20 border-amber-500/40 text-amber-300 animate-pulse"
                      : "bg-slate-900/40 border-slate-800 text-slate-600"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <div className="text-[11px] font-medium leading-tight">{s.label}</div>
                  <div className="text-[9px] uppercase tracking-wider font-mono">
                    {isPast ? "Done" : isCurrent ? "Active" : isReviewActive ? "Review" : "Pending"}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function JobDetailPage(props: JobDetailPageProps) {
  return (
    <React.Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
        </div>
      }
    >
      <JobDetailContent {...props} />
    </React.Suspense>
  );
}
