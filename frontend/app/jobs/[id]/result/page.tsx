"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, Job, SegmentItem } from "@/lib/api";
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
  RefreshCw,
  Subtitles,
  Eye,
  EyeOff
} from "lucide-react";

interface ResultPageProps {
  params: Promise<{ id: string }>;
}

function formatTimeSrt(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds - Math.floor(seconds)) * 1000);
  return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
}

function formatTimeVtt(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds - Math.floor(seconds)) * 1000);
  return `${String(hrs).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}.${String(ms).padStart(3, "0")}`;
}

function JobResultContent({ params }: ResultPageProps) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [job, setJob] = useState<Job | null>(null);
  const [segments, setSegments] = useState<SegmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Subtitle states
  const [subtitlesEnabled, setSubtitlesEnabled] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);

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
      fetchJobAndSegments();
    }
  }, [user, authLoading, jobId]);

  const fetchJobAndSegments = async () => {
    try {
      setLoading(true);
      setError(null);
      const [jobData, segData] = await Promise.all([
        api.getJob(jobId),
        api.getSegments(jobId).catch(() => [])
      ]);
      setJob(jobData);
      setSegments(segData);

      if (jobData.status === "completed") {
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

  // Subtitle download handlers
  const handleDownloadSrt = () => {
    if (!segments.length) return;
    const lines: string[] = [];
    segments.forEach((seg, idx) => {
      const text = seg.tgt_text || seg.src_text;
      const spkLabel = seg.speaker === "sheikh_ul_wazaif" ? "[Sheikh-ul-Wazaif] " : (seg.speaker === "narrator" ? "[Narrator] " : "");
      lines.push(String(idx + 1));
      lines.push(`${formatTimeSrt(seg.start)} --> ${formatTimeSrt(seg.end)}`);
      lines.push(`${spkLabel}${text}`);
      lines.push("");
    });
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lecture_subtitles_${jobId}.srt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadVtt = () => {
    if (!segments.length) return;
    const lines: string[] = ["WEBVTT", ""];
    segments.forEach((seg, idx) => {
      const text = seg.tgt_text || seg.src_text;
      const spkLabel = seg.speaker === "sheikh_ul_wazaif" ? "<v Sheikh-ul-Wazaif>" : (seg.speaker === "narrator" ? "<v Narrator>" : "");
      lines.push(String(idx + 1));
      lines.push(`${formatTimeVtt(seg.start)} --> ${formatTimeVtt(seg.end)}`);
      lines.push(`${spkLabel}${text}`);
      lines.push("");
    });
    const blob = new Blob([lines.join("\n")], { type: "text/vtt;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lecture_subtitles_${jobId}.vtt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Find active subtitle matching current playback position
  const activeSubtitle = segments.find(
    (s) => currentTime >= s.start && currentTime <= s.end
  );

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
          <h2 className="text-xl font-bold text-white">Error Loading Results</h2>
          <p className="text-zinc-400 text-sm">{error || "Job not found"}</p>
          <div className="pt-2">
            <Link
              href="/dashboard"
              className="px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-colors inline-block"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

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
        <div className="p-4 border-b border-zinc-800/80 bg-zinc-900/60 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-zinc-300">
            <Film className="w-4 h-4 text-indigo-400" />
            In-Browser Preview (Synchronized Stream-Copy MP4)
          </div>

          <div className="flex items-center gap-3">
            {/* Interactive Subtitle Button: Select / Unselect Captions */}
            <button
              onClick={() => setSubtitlesEnabled(!subtitlesEnabled)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all border ${
                subtitlesEnabled
                  ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30"
                  : "bg-zinc-800/80 border-zinc-700 text-zinc-400 hover:text-white hover:bg-zinc-700"
              }`}
              title="Click to toggle synchronized captions & subtitles on or off"
            >
              <Subtitles className="w-3.5 h-3.5" />
              <span>CC Subtitles:</span>
              <span className={`px-1.5 py-0.2 rounded font-bold uppercase text-[10px] ${subtitlesEnabled ? "bg-white/20 text-white" : "bg-zinc-700 text-zinc-400"}`}>
                {subtitlesEnabled ? "ON" : "OFF"}
              </span>
            </button>

            <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-medium">
              Sync Drift Verified (&lt; 0.5s)
            </span>
          </div>
        </div>

        {/* Video Player with Live Subtitle Overlay */}
        <div className="relative bg-black aspect-video flex items-center justify-center">
          <video
            controls
            playsInline
            preload="metadata"
            src={directVideoUrl}
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
            className="w-full h-full object-contain"
          >
            Your browser does not support HTML5 video streaming. Please download the MP4 file below.
          </video>

          {/* Subtitle Cue Overlay */}
          {subtitlesEnabled && activeSubtitle && (
            <div className="absolute bottom-12 left-1/2 -translate-x-1/2 max-w-[85%] text-center pointer-events-none z-10 transition-all duration-150">
              <div className="inline-block bg-black/90 text-white text-sm sm:text-base px-5 py-2.5 rounded-2xl backdrop-blur-md border border-white/15 shadow-2xl font-medium tracking-wide leading-relaxed">
                {activeSubtitle.speaker && (
                  <span className="text-amber-400 font-semibold mr-2">
                    [{activeSubtitle.speaker === "sheikh_ul_wazaif" ? "Sheikh-ul-Wazaif" : (activeSubtitle.speaker === "narrator" ? "Narrator" : activeSubtitle.speaker)}]:
                  </span>
                )}
                <span>{activeSubtitle.tgt_text || activeSubtitle.src_text}</span>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 bg-zinc-950/40 text-xs text-zinc-400 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4 flex-wrap">
            <span>Target: <strong className="text-white uppercase">{job.target_lang === "ur" ? "Urdu (اردو)" : "English (EN)"}</strong></span>
            <span>Neural Voice: <strong className="text-white">Multi-Speaker Piper (Ryan + Lessac)</strong></span>
            <span>Mastering: <strong className="text-white">-16 LUFS, -12dB Broadcast Ducking</strong></span>
            <span>Captions: <strong className={subtitlesEnabled ? "text-emerald-400 font-semibold" : "text-zinc-500"}>{subtitlesEnabled ? "Active Overlay" : "Disabled"}</strong></span>
          </div>
          <span className="text-zinc-500">Muxed via stream-copy with embedded soft subtitles</span>
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

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Option 1: MP4 Video */}
          <div className="bg-zinc-900 border border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
                <Film className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Dubbed Video</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Full synchronized lecture video with original slides, soft captions, & dubbed audio.
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
                <h3 className="font-semibold text-white text-base">Dubbed Audio</h3>
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
                <h3 className="font-semibold text-white text-base">Master Audio</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Uncompressed 44.1kHz 16-bit PCM master mix for studio post-production.
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

          {/* Option 4: Subtitles & Captions */}
          <div className="bg-zinc-900 border border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-5 flex flex-col justify-between transition-all group">
            <div className="space-y-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 group-hover:scale-105 transition-transform">
                <Subtitles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base">Closed Captions</h3>
                <p className="text-xs text-zinc-400 mt-1">
                  Synchronized bilingual subtitle tracks for YouTube, VLC, and video platforms.
                </p>
              </div>
            </div>

            <div className="pt-6 flex gap-2">
              <button
                onClick={handleDownloadSrt}
                className="flex-1 py-2.5 px-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 border border-zinc-700"
                title="Download standard SubRip Subtitle file"
              >
                <Download className="w-3.5 h-3.5" />
                .SRT
              </button>
              <button
                onClick={handleDownloadVtt}
                className="flex-1 py-2.5 px-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 border border-zinc-700"
                title="Download WebVTT file"
              >
                <Download className="w-3.5 h-3.5" />
                .VTT
              </button>
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
