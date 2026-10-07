"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, Job } from "@/lib/api";
import {
  Film,
  Music,
  Download,
  Share2,
  Copy,
  Check,
  ArrowLeft,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  FileCheck2,
  RefreshCw
} from "lucide-react";

interface ResultPageProps {
  params: Promise<{ id: string }>;
}

function JobResultContent({ params }: ResultPageProps) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Signed link states
  const [signedVideoUrl, setSignedVideoUrl] = useState<string | null>(null);
  const [signedAudioUrl, setSignedAudioUrl] = useState<string | null>(null);
  const [generatingLink, setGeneratingLink] = useState(false);
  const [copiedLink, setCopiedLink] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push(`/login?next=/jobs/${jobId}/result`);
      return;
    }

    if (user) {
      fetchJob();
    }
  }, [user, authLoading, jobId]);

  const fetchJob = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getJob(jobId);
      setJob(data);

      if (data.status === "completed") {
        // Pre-fetch signed links
        generateSignedUrls();
      }
    } catch (err: any) {
      setError(err.message || "Failed to load job results");
    } finally {
      setLoading(false);
    }
  };

  const generateSignedUrls = async () => {
    setGeneratingLink(true);
    try {
      const [videoRes, audioRes] = await Promise.all([
        api.getSignedDownloadUrl(jobId, "video"),
        api.getSignedDownloadUrl(jobId, "audio", "mp3")
      ]);
      setSignedVideoUrl(videoRes.download_url);
      setSignedAudioUrl(audioRes.download_url);
    } catch (err) {
      console.error("Failed to generate signed download link:", err);
    } finally {
      setGeneratingLink(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedLink(label);
    setTimeout(() => setCopiedLink(null), 3000);
  };

  if (authLoading || (loading && !job)) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-zinc-400 font-medium text-sm">Loading lecture dub artifacts...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-8 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="text-xl font-bold text-white">Unable to Load Dubbed Result</h2>
          <p className="text-zinc-400 text-sm">{error || "Job not found"}</p>
          <div className="pt-4 flex justify-center gap-4">
            <Link
              href="/dashboard"
              className="px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Back to Dashboard
            </Link>
            <button
              onClick={fetchJob}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // If job is not completed yet, direct to detail view
  if (job.status !== "completed") {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center space-y-5">
          <Clock className="w-12 h-12 text-amber-400 mx-auto animate-pulse" />
          <h2 className="text-xl font-bold text-white">Lecture Dubbing in Progress</h2>
          <p className="text-zinc-400 text-sm max-w-md mx-auto">
            This lecture job is currently at stage <span className="text-amber-400 font-semibold">{job.stage}</span> ({job.progress}%).
            Dubbed artifacts will be available once the synthesis and video muxing complete.
          </p>
          <div className="pt-3 flex justify-center gap-4">
            <Link
              href={`/jobs/${job.id}`}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-colors flex items-center gap-2"
            >
              Track Live Pipeline
            </Link>
            <Link
              href="/dashboard"
              className="px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const directVideoUrl = signedVideoUrl || api.getDownloadUrl(job.id, "video");
  const directMp3Url = signedAudioUrl || api.getDownloadUrl(job.id, "audio", "mp3");
  const directWavUrl = api.getDownloadUrl(job.id, "audio", "wav");

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      {/* Top Breadcrumb & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Link
              href={`/jobs/${job.id}`}
              className="p-2 -ml-2 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              Dubbed Result Ready
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            </h1>
          </div>
          <p className="text-sm text-zinc-400 pl-8">
            Job ID: <span className="font-mono text-xs text-zinc-300">{job.id}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href={`/jobs/${job.id}/review`}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 border border-zinc-700"
          >
            <FileCheck2 className="w-4 h-4 text-indigo-400" />
            Inspect Segments
          </Link>
          <Link
            href="/jobs/new"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-colors flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            Dub Another
          </Link>
        </div>
      </div>

      {/* Main Video Preview Player */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-zinc-800/80 bg-zinc-900/60 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-300">
            <Film className="w-4 h-4 text-indigo-400" />
            In-Browser Preview (Synchronized Stream-Copy MP4)
          </div>
          <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-medium">
            Sync Drift Verified (&lt; 0.5s)
          </span>
        </div>

        <div className="relative bg-black aspect-video flex items-center justify-center">
          <video
            controls
            playsInline
            preload="metadata"
            src={directVideoUrl}
            className="w-full h-full object-contain"
          >
            Your browser does not support HTML5 video streaming. Please download the MP4 file below.
          </video>
        </div>

        <div className="p-4 bg-zinc-950/40 text-xs text-zinc-400 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            <span>Target: <strong className="text-white uppercase">{job.target_lang === "ur" ? "Urdu (اردو)" : "English (EN)"}</strong></span>
            <span>Cloned Voice: <strong className="text-white">{job.options?.clone_voice ? "Enabled (ChatTTS/Coqui)" : "Disabled (Default)"}</strong></span>
            <span>Audio Mastering: <strong className="text-white">-16 LUFS, -12dB Ducking</strong></span>
          </div>
          <span className="text-zinc-500">Muxed via stream-copy with preserved high-definition video</span>
        </div>
      </div>

      {/* Download Center Options */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Download className="w-5 h-5 text-indigo-400" />
            Download Options
          </h2>
          <span className="text-xs text-zinc-500">No watermarks or quality restrictions</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Option 1: MP4 Video */}
          <div className="bg-zinc-900 border border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
                <Film className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Dubbed Video (MP4)</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Full synchronized lecture video with original slides & pristine dubbed audio.
                </p>
              </div>
            </div>

            <div className="pt-6">
              <a
                href={directVideoUrl}
                download={`lecture_dub_${job.id}.mp4`}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
              >
                <Download className="w-4 h-4" />
                Download MP4
              </a>
            </div>
          </div>

          {/* Option 2: MP3 Audio */}
          <div className="bg-zinc-900 border border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 group-hover:scale-105 transition-transform">
                <Music className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Dubbed Audio (MP3)</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Lightweight 192kbps MP3 audio with balanced speech and background mix.
                </p>
              </div>
            </div>

            <div className="pt-6">
              <a
                href={directMp3Url}
                download={`lecture_dub_${job.id}.mp3`}
                className="w-full py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2 border border-zinc-700"
              >
                <Download className="w-4 h-4" />
                Download MP3
              </a>
            </div>
          </div>

          {/* Option 3: WAV Master */}
          <div className="bg-zinc-900 border border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-105 transition-transform">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Master Audio (WAV)</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Uncompressed 48kHz 16-bit PCM master mix for studio post-production.
                </p>
              </div>
            </div>

            <div className="pt-6">
              <a
                href={directWavUrl}
                download={`lecture_dub_${job.id}.wav`}
                className="w-full py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2 border border-zinc-700"
              >
                <Download className="w-4 h-4" />
                Download WAV
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Shareable Signed Links */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="font-bold text-white text-base flex items-center gap-2">
              <Share2 className="w-4 h-4 text-indigo-400" />
              Temporary Shareable Download Link
            </h3>
            <p className="text-xs text-zinc-400">
              Cryptographically signed download URL valid for 60 minutes. Recipient does not need an account.
            </p>
          </div>
          <button
            onClick={generateSignedUrls}
            disabled={generatingLink}
            className="text-xs px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg flex items-center gap-1.5 transition-colors border border-zinc-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generatingLink ? "animate-spin" : ""}`} />
            Refresh Link
          </button>
        </div>

        <div className="space-y-3 pt-2">
          {/* Video Share link */}
          <div className="space-y-1">
            <label className="text-xs text-zinc-400 font-medium">MP4 Video Link (Expires in 1 hour)</label>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={signedVideoUrl || "Generating signed URL..."}
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs font-mono text-zinc-300 select-all outline-none focus:border-indigo-500"
              />
              <button
                onClick={() => signedVideoUrl && copyToClipboard(signedVideoUrl, "video")}
                disabled={!signedVideoUrl}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-medium transition-colors flex items-center gap-1.5 shrink-0"
              >
                {copiedLink === "video" ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-300" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Link
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Audio Share link */}
          <div className="space-y-1">
            <label className="text-xs text-zinc-400 font-medium">MP3 Audio Link (Expires in 1 hour)</label>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={signedAudioUrl || "Generating signed URL..."}
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs font-mono text-zinc-300 select-all outline-none focus:border-indigo-500"
              />
              <button
                onClick={() => signedAudioUrl && copyToClipboard(signedAudioUrl, "audio")}
                disabled={!signedAudioUrl}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-white rounded-xl text-xs font-medium transition-colors flex items-center gap-1.5 shrink-0 border border-zinc-700"
              >
                {copiedLink === "audio" ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-300" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Link
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function JobResultPage(props: ResultPageProps) {
  return (
    <React.Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
        </div>
      }
    >
      <JobResultContent {...props} />
    </React.Suspense>
  );
}
