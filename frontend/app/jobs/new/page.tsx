"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { 
  Upload, 
  Link as LinkIcon, 
  HardDrive, 
  Sparkles, 
  ShieldAlert, 
  AlertCircle, 
  CheckCircle2, 
  ArrowRight,
  Info
} from "lucide-react";

export default function NewJobPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [tab, setTab] = useState<"upload" | "link">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [linkUrl, setLinkUrl] = useState("");
  const [targetLang, setTargetLang] = useState("ur");
  const [sourceLang, setSourceLang] = useState("en");
  const [cloneVoice, setCloneVoice] = useState(true);
  const [skipReview, setSkipReview] = useState(false);
  const [generateSubtitles, setGenerateSubtitles] = useState(true);
  const [ownershipConfirmed, setOwnershipConfirmed] = useState(false);
  const [voiceConsent, setVoiceConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      const ext = selected.name.split(".").pop()?.toLowerCase();
      if (!["mp4", "mov", "mkv", "webm"].includes(ext || "")) {
        setError("Invalid video format. Supported formats: MP4, MOV, MKV, WEBM.");
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!ownershipConfirmed) {
      setError("You must confirm copyright ownership or permission to translate this lecture.");
      return;
    }

    if (cloneVoice && !voiceConsent) {
      setError("Voice cloning requires confirming that the original speaker consented to voice cloning.");
      return;
    }

    setLoading(true);

    try {
      let sourceRef = "";
      let sourceType: "upload" | "url" | "youtube" | "drive" | "dropbox" = "upload";

      if (tab === "upload") {
        if (!file) {
          setError("Please select a lecture video file to upload.");
          setLoading(false);
          return;
        }

        // Chunked upload
        setUploadProgress(0);
        const init = await api.initUpload(file.name, file.size, file.type || "video/mp4");
        const uploadId = init.upload_id;
        const chunkSize = init.chunk_size || 5 * 1024 * 1024;

        let offset = 0;
        while (offset < file.size) {
          const chunk = file.slice(offset, offset + chunkSize);
          const res = await api.uploadChunk(uploadId, chunk, offset, (uploaded) => {
            setUploadProgress(Math.round((uploaded / file.size) * 100));
          });
          offset = (res && typeof res.offset === "number" && res.offset > offset)
            ? res.offset
            : offset + chunk.size;
        }

        // Complete upload assembly
        try {
          await api.completeUpload(uploadId);
        } catch (compErr: any) {
          console.warn("Upload complete notice:", compErr);
        }

        sourceRef = uploadId;
        sourceType = "upload";
      } else {
        if (!linkUrl.trim()) {
          setError("Please enter a valid video URL or share link.");
          setLoading(false);
          return;
        }

        sourceRef = linkUrl.trim();
        if (sourceRef.includes("youtube.com") || sourceRef.includes("youtu.be")) {
          sourceType = "youtube";
        } else if (sourceRef.includes("drive.google.com")) {
          sourceType = "drive";
        } else if (sourceRef.includes("dropbox.com")) {
          sourceType = "dropbox";
        } else {
          sourceType = "url";
        }
      }

      // Create Job
      const job = await api.createJob({
        source_type: sourceType,
        source_ref: sourceRef,
        target_lang: targetLang,
        source_lang: sourceLang === "auto" ? undefined : sourceLang,
        clone_voice: cloneVoice,
        skip_review: skipReview,
        generate_subtitles: generateSubtitles,
        ownership_confirmed: ownershipConfirmed,
        voice_consent: voiceConsent,
      });

      router.push(`/jobs/${job.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start lecture dubbing job.");
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <Sparkles className="w-7 h-7 text-indigo-400" />
          Queue New Lecture Dub
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload an educational video or import from a share link. The job will separate speech, translate, and pause for your review before voice synthesis.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Step 1: Video Source Input */}
        <div className="glass-panel p-6 rounded-2xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-indigo-600/20 text-indigo-400 text-xs flex items-center justify-center font-bold">1</span>
              Source Lecture Video
            </h2>
            <div className="flex items-center bg-slate-900 p-1 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setTab("upload")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                  tab === "upload" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                <Upload className="w-3.5 h-3.5" />
                File Upload
              </button>
              <button
                type="button"
                onClick={() => setTab("link")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                  tab === "link" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                <LinkIcon className="w-3.5 h-3.5" />
                URL / Cloud Link
              </button>
            </div>
          </div>

          {tab === "upload" ? (
            <div className="space-y-4">
              <label className="border-2 border-dashed border-slate-700/80 hover:border-indigo-500/50 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all bg-slate-900/40 hover:bg-slate-900/80 group">
                <input
                  type="file"
                  accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="w-12 h-12 rounded-xl bg-indigo-600/10 text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <Upload className="w-6 h-6" />
                </div>
                {file ? (
                  <div className="text-center">
                    <div className="text-sm font-semibold text-white">{file.name}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {(file.size / (1024 * 1024)).toFixed(1)} MB • Click to replace
                    </div>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="text-sm font-medium text-slate-200">
                      Click to choose or drag lecture video file here
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      MP4, MOV, MKV, or WebM (standard max duration 90 min)
                    </div>
                  </div>
                )}
              </label>

              {uploadProgress !== null && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Uploading chunk stream...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
                    <div className="h-full bg-indigo-500 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <label className="block text-xs font-medium text-slate-300">
                Direct Video URL or Cloud Share Link
              </label>
              <div className="relative">
                <input
                  type="url"
                  value={linkUrl}
                  onChange={(e) => setLinkUrl(e.target.value)}
                  placeholder="https://drive.google.com/file/d/... or YouTube / Dropbox URL"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>
              <p className="text-[11px] text-slate-500 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5" />
                Supports direct HTTPS video links, Google Drive share links, Dropbox share links, and educational YouTube URLs.
              </p>
            </div>
          )}
        </div>

        {/* Step 2: Language & Dubbing Settings */}
        <div className="glass-panel p-6 rounded-2xl space-y-5">
          <h2 className="text-base font-semibold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <span className="w-6 h-6 rounded-full bg-indigo-600/20 text-indigo-400 text-xs flex items-center justify-center font-bold">2</span>
            Language & Dubbing Configuration
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Target Dubbing Language
              </label>
              <select
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="ur">Urdu (اردو) — Natural Piper ONNX & Tone Transfer</option>
                <option value="en">English (US/UK) — MeloTTS & OpenVoice</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Original Lecture Language
              </label>
              <select
                value={sourceLang}
                onChange={(e) => setSourceLang(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="en">English (default)</option>
                <option value="ur">Urdu</option>
                <option value="auto">Auto-Detect via Faster-Whisper</option>
              </select>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <label className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition-colors">
              <input
                type="checkbox"
                checked={cloneVoice}
                onChange={(e) => setCloneVoice(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
              />
              <div>
                <div className="text-sm font-medium text-white flex items-center gap-1.5">
                  Clone Original Speaker's Voice
                  <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400">
                    Recommended
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Extracts a 15-second speech reference from separated vocals and transfers speaker timbre into the dubbed audio.
                </div>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition-colors">
              <input
                type="checkbox"
                checked={generateSubtitles}
                onChange={(e) => setGenerateSubtitles(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
              />
              <div>
                <div className="text-sm font-medium text-white flex items-center gap-1.5">
                  Generate Closed Captions & Subtitles
                  <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400">
                    CC Subtitles
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Generates time-aligned .SRT / .VTT subtitles and embeds soft closed captions toggleable on/off in the player.
                </div>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition-colors">
              <input
                type="checkbox"
                checked={skipReview}
                onChange={(e) => setSkipReview(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
              />
              <div>
                <div className="text-sm font-medium text-white">
                  Skip Human Review Gate (Fully Automated)
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Synthesizes speech immediately upon translation without pausing at the interactive side-by-side review editor.
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Step 3: Legal & Compliance Attestations */}
        <div className="glass-panel p-6 rounded-2xl space-y-4 border-amber-500/20 bg-amber-500/[0.02]">
          <h2 className="text-base font-semibold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-xs flex items-center justify-center font-bold">3</span>
            Required Legal & Rights Attestation
          </h2>

          <div className="space-y-3">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                required
                checked={ownershipConfirmed}
                onChange={(e) => setOwnershipConfirmed(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
              />
              <span className="text-xs text-slate-300 leading-relaxed">
                I certify that I am the copyright owner of this lecture material or have explicit authorization from the copyright holder to create and distribute translated derivative dubs.
              </span>
            </label>

            {cloneVoice && (
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  required
                  checked={voiceConsent}
                  onChange={(e) => setVoiceConsent(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
                />
                <span className="text-xs text-slate-300 leading-relaxed">
                  I certify that the original speaker consented to the use of their voice for educational voice cloning and tone synthesis.
                </span>
              </label>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 px-6 rounded-xl font-medium text-white bg-indigo-600 hover:bg-indigo-500 shadow-xl shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-base"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                Processing & Starting Job...
              </span>
            ) : (
              <>
                Start Lecture Dubbing Pipeline
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
