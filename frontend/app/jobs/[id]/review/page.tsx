"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, Job, SegmentItem } from "@/lib/api";
import { 
  FileCheck2, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowLeft, 
  Save, 
  Clock, 
  Sparkles, 
  Layers, 
  ArrowRight,
  Filter
} from "lucide-react";

interface ReviewEditorPageProps {
  params: Promise<{ id: string }>;
}

function ReviewEditorContent({ params }: ReviewEditorPageProps) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const router = useRouter();

  const [job, setJob] = useState<Job | null>(null);
  const [segments, setSegments] = useState<SegmentItem[]>([]);
  const [editedTexts, setEditedTexts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [filterFlaggedOnly, setFilterFlaggedOnly] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [jobData, segsData] = await Promise.all([
          api.getJob(jobId),
          api.getSegments(jobId),
        ]);
        setJob(jobData);
        setSegments(segsData);

        const initialEdits: Record<string, string> = {};
        segsData.forEach((s) => {
          initialEdits[s.id] = s.tgt_text;
        });
        setEditedTexts(initialEdits);
      } catch (err) {
        console.error("Failed to load review data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [jobId]);

  const handleTextChange = (id: string, text: string) => {
    setEditedTexts((prev) => ({ ...prev, [id]: text }));
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const updates = Object.entries(editedTexts).map(([id, tgt_text]) => ({
        id,
        tgt_text,
      }));
      const updated = await api.updateSegments(jobId, updates);
      setSegments(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert("Failed to save segment edits: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    setApproving(true);
    try {
      // Save any pending edits first
      await handleSave();
      // Approve job to begin voice synthesis
      await api.approveJob(jobId);
      router.push(`/jobs/${jobId}`);
    } catch (err: any) {
      alert("Failed to approve job: " + err.message);
      setApproving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24 text-slate-400 gap-3">
        <span className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></span>
        Loading translation segments for review...
      </div>
    );
  }

  const flaggedCount = segments.filter((s) => s.flagged).length;

  const displaySegments = filterFlaggedOnly
    ? segments.filter((s) => s.flagged)
    : [...segments].sort((a, b) => {
        // Flagged segments float to the top
        if (a.flagged && !b.flagged) return -1;
        if (!a.flagged && b.flagged) return 1;
        return a.idx - b.idx;
      });

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <Link
            href={`/jobs/${jobId}`}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Job Overview
          </Link>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <FileCheck2 className="w-6 h-6 text-amber-400" />
            Side-by-Side Segment Review Editor
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Total Segments: {segments.length} • Flagged for Inspection: {flaggedCount}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setFilterFlaggedOnly(!filterFlaggedOnly)}
            className={`px-3 py-2 rounded-xl text-xs font-medium border flex items-center gap-1.5 transition-colors ${
              filterFlaggedOnly
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            {filterFlaggedOnly ? "Showing Flagged Only" : "Filter Flagged Items"}
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : saveSuccess ? "Saved!" : "Save Edits"}
          </button>

          <button
            onClick={handleApprove}
            disabled={approving}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all disabled:opacity-50"
          >
            {approving ? (
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                Approve & Start Voice Dubbing
              </>
            )}
          </button>
        </div>
      </div>

      {/* Editor Grid Header */}
      <div className="hidden lg:grid grid-cols-12 gap-4 px-4 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-900">
        <div className="col-span-1"># & Time</div>
        <div className="col-span-5">Original Source Speech ({job?.source_lang || "English"})</div>
        <div className="col-span-6">Translated Dub Text ({job?.target_lang === "ur" ? "Urdu RTL" : "English"})</div>
      </div>

      {/* Segments List */}
      <div className="space-y-4">
        {displaySegments.map((seg) => {
          const isUrdu = job?.target_lang === "ur";
          const currentText = editedTexts[seg.id] ?? seg.tgt_text;
          const isEdited = currentText !== seg.tgt_text || seg.edited_by_user;

          return (
            <div
              key={seg.id}
              className={`glass-panel p-4 rounded-2xl transition-all ${
                seg.flagged
                  ? "border-amber-500/40 bg-amber-500/[0.03]"
                  : "border-slate-800/80 hover:border-slate-700"
              }`}
            >
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
                {/* Meta column */}
                <div className="lg:col-span-1 space-y-1">
                  <div className="text-xs font-bold text-slate-300">
                    Seg #{seg.idx}
                  </div>
                  <div className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Dur: {(seg.end - seg.start).toFixed(1)}s
                  </div>
                  {seg.flagged && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      <AlertTriangle className="w-3 h-3" />
                      Flagged
                    </span>
                  )}
                </div>

                {/* Source text column */}
                <div className="lg:col-span-5 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                  {seg.src_text}
                </div>

                {/* Target text editor column */}
                <div className="lg:col-span-6 space-y-2">
                  {seg.flagged && seg.flag_reason && (
                    <div className="text-xs text-amber-300/90 bg-amber-500/10 px-3 py-1.5 rounded-lg border border-amber-500/20 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>Flag reason: {seg.flag_reason}</span>
                    </div>
                  )}

                  <textarea
                    rows={3}
                    dir={isUrdu ? "rtl" : "ltr"}
                    value={currentText}
                    onChange={(e) => handleTextChange(seg.id, e.target.value)}
                    className={`w-full p-3 rounded-xl bg-slate-950/80 border text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
                      isUrdu ? "urdu-text" : ""
                    } ${
                      isEdited
                        ? "border-indigo-500/50 ring-1 ring-indigo-500/30"
                        : "border-slate-800"
                    }`}
                    placeholder="Enter translated speech sentence..."
                  />

                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>
                      Length: {currentText.length} characters
                    </span>
                    {isEdited && (
                      <span className="text-indigo-400 font-medium">
                        Edited by reviewer
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Floating Bottom Bar */}
      <div className="sticky bottom-4 z-40 p-4 rounded-2xl glass-panel flex items-center justify-between gap-4 border border-indigo-500/30 shadow-2xl">
        <div className="text-xs text-slate-300 hidden sm:block">
          Reviewing translations ensures accurate technical terms and learner comprehension.
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-200 text-xs font-semibold flex items-center gap-1.5"
          >
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : saveSuccess ? "Saved!" : "Save Edits"}
          </button>
          <button
            onClick={handleApprove}
            disabled={approving}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-indigo-600/30 flex items-center gap-2"
          >
            {approving ? (
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                Approve & Start Voice Dubbing
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ReviewEditorPage(props: ReviewEditorPageProps) {
  return (
    <React.Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
        </div>
      }
    >
      <ReviewEditorContent {...props} />
    </React.Suspense>
  );
}
