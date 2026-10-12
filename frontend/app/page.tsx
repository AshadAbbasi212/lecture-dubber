import React from "react";
import Link from "next/link";
import { 
  Sparkles, 
  Cpu, 
  Languages, 
  Mic2, 
  Music, 
  SlidersHorizontal, 
  ArrowRight, 
  ShieldCheck, 
  CheckCircle2,
  FileCheck2
} from "lucide-react";
import VoiceGallery from "@/components/VoiceGallery";

export default function HomePage() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-24 md:pt-28 md:pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full text-center">
        {/* Glow decoration */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none -z-10" />

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-8">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Local-First AI Dubbing for Global Learning</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight max-w-4xl mx-auto leading-[1.15]">
          Translate Educational Lectures into{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400">
            Native Cloned Voices
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Preserve background audio, enforce technical glossary accuracy, and review Urdu or English translations before synthesis. 100% locally on your NVIDIA GPU.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/jobs/new"
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl font-bold text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 shadow-xl shadow-indigo-600/35 transition-all flex items-center justify-center gap-2 group text-base btn-3d"
          >
            Start Dubbing Lecture
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl font-semibold text-slate-200 hover:text-white bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 transition-all text-base shadow-lg"
          >
            View Dashboard
          </Link>
        </div>

        {/* Badges / Guarantees */}
        <div className="mt-12 pt-8 border-t border-slate-900 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto text-xs text-slate-400">
          <div className="flex items-center justify-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Commercial License</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Zero Cloud API Leakage</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Human Review Gate</span>
          </div>
          <div className="flex items-center justify-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Sample-Accurate Sync</span>
          </div>
        </div>
      </section>

      {/* Feature Architecture Cards */}
      <section id="features" className="py-20 border-t border-slate-900 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-white tracking-tight">
              An End-to-End Pipeline Built for Academics
            </h2>
            <p className="mt-4 text-slate-400 text-sm sm:text-base">
              Every stage runs sequentially with crash checkpointing, ensuring full idempotency for 30–60 minute lectures.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 perspective-1000">
            <div className="glass-panel card-3d p-6 rounded-2xl space-y-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/10">
                <Music className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Demucs Stem Isolation</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Separates voice from blackboard room tone, lab background, and presentation music. Background audio is dynamically ducked by -12 dB during speech.
              </p>
            </div>

            <div className="glass-panel card-3d p-6 rounded-2xl space-y-4">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center shadow-lg shadow-cyan-500/10">
                <Languages className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Length-Budgeted Translation</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Qwen2.5 translates sentences under a strict character length budget based on target language speaking rate, automatically generating shorter variants when needed.
              </p>
            </div>

            <div className="glass-panel card-3d p-6 rounded-2xl space-y-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-500/10">
                <Mic2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Speaker Timbre Transfer</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Extracts a clean reference clip from the original speaker to transfer their vocal tone color into Urdu or English, keeping lectures authentic and engaging.
              </p>
            </div>

            <div className="glass-panel card-3d p-6 rounded-2xl space-y-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shadow-lg shadow-amber-500/10">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Review & Meaning-Drift Check</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Automatically flags semantic drift and terminology anomalies. Review translations side-by-side with full RTL Urdu editor support before synthesis.
              </p>
            </div>

            <div className="glass-panel card-3d p-6 rounded-2xl space-y-4">
              <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center shadow-lg shadow-rose-500/10">
                <SlidersHorizontal className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Intelligent Timing Fit</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Binds stretch ratios to a natural 1.25x maximum cap and borrows adjacent silence intervals to eliminate artificial chipmunk or robotic sound.
              </p>
            </div>

            <div className="glass-panel card-3d p-6 rounded-2xl space-y-4">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shadow-lg shadow-purple-500/10">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Stream-Copy Muxing</h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Preserves original 1080p/4K video frames without generational compression artifacts, muxing with EBU R128 (-16 LUFS) mastered audio in seconds.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Voice Showcase Gallery Section */}
      <section id="voices" className="py-20 border-t border-slate-900 bg-slate-950/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Studio-Grade Neural TTS</span>
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">
              Audition 22 Authentic Neural Voices
            </h2>
            <p className="mt-3 text-slate-400 text-sm sm:text-base">
              Listen to native audio samples across 12 educational languages with human cadence, warmth, and pitch realism.
            </p>
          </div>
          <div className="bg-slate-900/40 p-6 md:p-8 rounded-3xl border border-slate-800 shadow-2xl">
            <VoiceGallery />
          </div>
        </div>
      </section>
    </div>
  );
}
