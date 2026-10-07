import React from "react";
import Link from "next/link";
import { ShieldCheck, HardDrive, Cpu, Terminal } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/60 mt-auto py-8 text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="space-y-3">
            <div className="font-semibold text-sm text-slate-300 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              100% Local Processing
            </div>
            <p className="text-slate-400 leading-relaxed">
              No cloud AI dependencies. Translation, transcription, stem separation, and voice synthesis run completely offline on your own GPU.
            </p>
          </div>

          <div className="space-y-3">
            <div className="font-semibold text-sm text-slate-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Educational Rights
            </div>
            <p className="text-slate-400 leading-relaxed">
              Strict consent verification and copyright attestations ensure compliance with educational and commercial fair use standards.
            </p>
          </div>

          <div className="space-y-3">
            <div className="font-semibold text-sm text-slate-300 flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-cyan-400" />
              Privacy & Retention
            </div>
            <p className="text-slate-400 leading-relaxed">
              Audio stems and raw uploads are isolated per user and automatically purged according to local storage retention rules.
            </p>
          </div>

          <div className="space-y-3">
            <div className="font-semibold text-sm text-slate-300">Compliance & Legal</div>
            <ul className="space-y-2">
              <li>
                <Link href="/terms" className="hover:text-slate-300 transition-colors">
                  Terms of Service & AI Use
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-slate-300 transition-colors">
                  Privacy Policy & Data Retention
                </Link>
              </li>
              <li>
                <Link href="/takedown" className="hover:text-slate-300 transition-colors">
                  Copyright & Takedown Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            &copy; 2026 Lecture Dubber. Built with Faster-Whisper, Qwen2.5, Demucs & OpenVoice.
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Local Engine Online
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
