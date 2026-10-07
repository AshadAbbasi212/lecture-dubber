"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, Job } from "@/lib/api";
import { 
  Layers, 
  PlusCircle, 
  RefreshCw, 
  Clock, 
  ArrowRight, 
  FileCheck, 
  Download, 
  Trash2, 
  Video, 
  HardDrive, 
  Link as LinkIcon, 
  AlertCircle, 
  CheckCircle2, 
  Hourglass, 
  Sliders 
} from "lucide-react";

function YoutubeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
    </svg>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      const data = await api.listJobs();
      setJobs(data);
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
      return;
    }
    if (user) {
      fetchJobs();
      const interval = setInterval(fetchJobs, 6000);
      return () => clearInterval(interval);
    }
  }, [user, authLoading, router]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this job and all associated audio/video files?")) return;
    setDeletingId(id);
    try {
      await api.deleteJob(id);
      setJobs(jobs.filter((j) => j.id !== id));
    } catch (err: any) {
      alert("Failed to delete job: " + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case "youtube": return <YoutubeIcon className="w-4 h-4 text-red-400" />;
      case "drive":
      case "dropbox": return <HardDrive className="w-4 h-4 text-cyan-400" />;
      case "url": return <LinkIcon className="w-4 h-4 text-indigo-400" />;
      default: return <Video className="w-4 h-4 text-slate-300" />;
    }
  };

  const getStatusBadge = (status: string, stage: string) => {
    switch (status) {
      case "awaiting_review":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 animate-pulse">
            <FileCheck className="w-3.5 h-3.5" />
            Review Needed
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
            Running: {stage}
          </span>
        );
      case "queued":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/15 text-slate-300 border border-slate-500/30">
            <Hourglass className="w-3.5 h-3.5" />
            Queued
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Completed
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
            <AlertCircle className="w-3.5 h-3.5" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400">
            {status}
          </span>
        );
    }
  };

  const filteredJobs = jobs.filter((j) => {
    if (filter === "review") return j.status === "awaiting_review";
    if (filter === "running") return j.status === "running" || j.status === "queued";
    if (filter === "completed") return j.status === "completed";
    return true;
  });

  if (authLoading || loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-20 text-slate-400 gap-3">
        <span className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>
        Loading lecture dubbing jobs...
      </div>
    );
  }

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-indigo-400" />
            Lecture Dubbing Dashboard
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Track AI translation, review segments, and download final dubbed media.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchJobs}
            className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Refresh jobs"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            href="/jobs/new"
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm shadow-lg shadow-indigo-600/25 flex items-center gap-2 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            New Lecture Dub
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 overflow-x-auto">
        {[
          { key: "all", label: `All Jobs (${jobs.length})` },
          { key: "review", label: `Awaiting Review (${jobs.filter((j) => j.status === "awaiting_review").length})` },
          { key: "running", label: `Active (${jobs.filter((j) => j.status === "running" || j.status === "queued").length})` },
          { key: "completed", label: `Completed (${jobs.filter((j) => j.status === "completed").length})` },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
              filter === tab.key
                ? "bg-slate-800 text-white border border-slate-700"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Jobs List */}
      {filteredJobs.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <Video className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">No jobs found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              {filter === "all"
                ? "You haven't queued any lecture videos yet. Start by uploading or importing your first video."
                : "No lecture jobs match this filter."}
            </p>
          </div>
          <Link
            href="/jobs/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Create First Dub Job
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredJobs.map((job) => (
            <div
              key={job.id}
              onClick={() => {
                if (job.status === "awaiting_review") {
                  router.push(`/jobs/${job.id}/review`);
                } else if (job.status === "completed") {
                  router.push(`/jobs/${job.id}/result`);
                } else {
                  router.push(`/jobs/${job.id}`);
                }
              }}
              className="glass-panel glass-panel-hover p-5 rounded-2xl cursor-pointer space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                    {getSourceIcon(job.source_type)}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white flex items-center gap-2">
                      <span className="truncate max-w-[280px] sm:max-w-[450px]">
                        {job.source_ref}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300">
                        {job.source_lang || "en"} → {job.target_lang}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-3 mt-1">
                      <span>Created {new Date(job.created_at).toLocaleString()}</span>
                      {job.options?.clone_voice && (
                        <span className="text-indigo-400 flex items-center gap-1 text-[11px]">
                          • Cloned Voice Active
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  {getStatusBadge(job.status, job.stage)}
                  <button
                    onClick={(e) => handleDelete(job.id, e)}
                    disabled={deletingId === job.id}
                    className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
                    title="Delete job"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="capitalize">
                    Stage: <span className="text-slate-200 font-medium">{job.stage}</span>
                  </span>
                  <div className="flex items-center gap-3">
                    {job.estimated_seconds_remaining && job.estimated_seconds_remaining > 0 ? (
                      <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                        <Clock className="w-3.5 h-3.5" />
                        ~{Math.ceil(job.estimated_seconds_remaining / 60)} min remaining
                      </span>
                    ) : null}
                    <span className="font-semibold text-slate-200">{job.progress}%</span>
                  </div>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
                  <div
                    className={`h-full transition-all duration-500 ${
                      job.status === "completed"
                        ? "bg-emerald-500"
                        : job.status === "failed"
                        ? "bg-rose-500"
                        : job.status === "awaiting_review"
                        ? "bg-amber-500"
                        : "bg-indigo-600"
                    }`}
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-900 text-xs">
                <span className="text-slate-500">ID: {job.id.substring(0, 8)}...</span>
                <div className="flex items-center gap-2">
                  {job.status === "awaiting_review" ? (
                    <span className="text-amber-400 font-medium flex items-center gap-1 hover:underline">
                      Review Translations Now <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  ) : job.status === "completed" ? (
                    <span className="text-emerald-400 font-medium flex items-center gap-1 hover:underline">
                      Watch & Download Output <Download className="w-3.5 h-3.5" />
                    </span>
                  ) : (
                    <span className="text-slate-400 flex items-center gap-1 hover:text-white">
                      View Pipeline Details <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
