import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowLeft, Lock, Trash2, HardDrive, EyeOff } from "lucide-react";

export const metadata = {
  title: "Privacy Policy | Lecture Dubber",
  description: "Privacy and Data Retention Policy for the Lecture Dubber Local Platform.",
};

export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 space-y-8">
      <div className="space-y-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-emerald-400" />
          <h1 className="text-3xl font-extrabold text-white">Privacy Policy</h1>
        </div>
        <p className="text-sm text-zinc-400">
          Last updated: October 2026 • Local-First Architecture
        </p>
      </div>

      {/* Prominent Legal Review Notice */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-5 flex items-start gap-4 text-amber-200">
        <Lock className="w-6 h-6 shrink-0 mt-0.5 text-amber-400" />
        <div className="text-sm space-y-1">
          <p className="font-semibold text-amber-300">
            [NOTICE: DRAFT TEMPLATE — PENDING FORMAL LEGAL COUNSEL REVIEW]
          </p>
          <p className="text-amber-200/80 text-xs leading-relaxed">
            This Privacy Policy details how data is stored, isolated, and retained on local-first Lecture Dubber deployments. Adjust this policy to match institutional or cloud hosting configurations.
          </p>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8 text-zinc-300 text-sm leading-relaxed">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-base">1.</span> Local-First Processing Commitment
          </h2>
          <p>
            Lecture Dubber is engineered with privacy as a foundational principle. All automated speech recognition (Faster-Whisper), background audio stem separation (Demucs), machine translation (local LLM), and speech synthesis (ChatTTS / Coqui XTTS v2) execute entirely on your designated local hardware or private instance.
          </p>
          <p className="font-medium text-emerald-400/90">
            ✓ No audio, video, or lecture transcripts are ever uploaded to third-party hosted commercial AI APIs or remote training clusters.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-base">2.</span> Information We Collect &amp; Store
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-zinc-400">
            <li>
              <strong className="text-zinc-200">Account Credentials:</strong> Email addresses and cryptographic password hashes (Argon2id). Passwords are never stored in plaintext.
            </li>
            <li>
              <strong className="text-zinc-200">Lecture Media Files:</strong> Video and audio inputs uploaded by you or imported from verified share URLs.
            </li>
            <li>
              <strong className="text-zinc-200">Pipeline Artifacts:</strong> Extracted audio stems (vocals, accompaniment), Whisper sentence segments, translated texts, acoustic speaker embeddings, and muxed output MP4/MP3 files.
            </li>
            <li>
              <strong className="text-zinc-200">Compliance Records:</strong> Digital attestation records confirming speaker consent and copyright ownership at job creation.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-base">3.</span> Storage Isolation &amp; Security Controls
          </h2>
          <p>
            Media files and pipeline artifacts are partitioned in dedicated per-job storage paths. Direct filesystem traversal is strictly prevented via pathname sanitization. Access to job artifacts requires authenticated JWT session tokens or short-lived signed download tokens.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-base">4.</span> Ephemeral Retention &amp; Automatic Cleanup
          </h2>
          <p>
            To conserve disk space and protect speaker privacy:
          </p>
          <ul className="list-disc pl-5 space-y-2 text-zinc-400">
            <li>
              <strong className="text-zinc-200">Automated Purging:</strong> Raw uploads and intermediate separation stems may be scheduled for automatic deletion after 7 days (configurable via <code className="text-zinc-300 font-mono text-xs">STORAGE_RETENTION_DAYS</code>).
            </li>
            <li>
              <strong className="text-zinc-200">Immediate Manual Deletion:</strong> You can delete any job and all associated disk artifacts immediately at any time through the Dashboard or Job Detail screen.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-base">5.</span> No Model Training on User Data
          </h2>
          <p>
            Your uploaded lecture videos, voice recordings, and customized review segment corrections are never used to train or fine-tune public foundation models. All model weights deployed on the instance are frozen upstream releases.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-base">6.</span> Contacting Privacy Administration
          </h2>
          <p>
            If you have questions about data handling, local storage retention, or wish to request full account erasure, email{" "}
            <span className="text-emerald-400 font-mono">privacy@lecturedubber.local</span>.
          </p>
        </section>
      </div>
    </div>
  );
}
