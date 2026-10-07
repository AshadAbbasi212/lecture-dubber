import React from "react";
import Link from "next/link";
import { ShieldAlert, ArrowLeft, FileText, Scale } from "lucide-react";

export const metadata = {
  title: "Terms of Service | Lecture Dubber",
  description: "Terms of Service and Voice Synthesis Compliance Agreement for Lecture Dubber.",
};

export default function TermsPage() {
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
          <Scale className="w-8 h-8 text-indigo-400" />
          <h1 className="text-3xl font-extrabold text-white">Terms of Service</h1>
        </div>
        <p className="text-sm text-zinc-400">
          Last updated: October 2026 • Effective immediately
        </p>
      </div>

      {/* Prominent Legal Review Notice */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-5 flex items-start gap-4 text-amber-200">
        <ShieldAlert className="w-6 h-6 shrink-0 mt-0.5 text-amber-400" />
        <div className="text-sm space-y-1">
          <p className="font-semibold text-amber-300">
            [NOTICE: DRAFT TEMPLATE — PENDING FORMAL LEGAL COUNSEL REVIEW]
          </p>
          <p className="text-amber-200/80 text-xs leading-relaxed">
            This document outlines the standard operational and ethical terms for the Lecture Dubber AI-assisted dubbing engine. Consult qualified legal counsel before deploying in commercial educational jurisdictions.
          </p>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8 text-zinc-300 text-sm leading-relaxed">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">1.</span> Acceptance of Terms
          </h2>
          <p>
            By accessing or using Lecture Dubber (&quot;the Platform&quot;, &quot;Service&quot;), you agree to be legally bound by these Terms of Service. If you are entering into this agreement on behalf of an educational institution, corporation, or other legal entity, you represent that you have the authority to bind such entity.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">2.</span> Voice Cloning &amp; Speaker Consent Obligations
          </h2>
          <p>
            Lecture Dubber provides neural voice cloning and speech synthesis features designed strictly for educational accessibility and lecture translation.
          </p>
          <ul className="list-disc pl-5 space-y-2 text-zinc-400">
            <li>
              <strong className="text-zinc-200">Affirmative Consent:</strong> You represent and warrant that you hold explicit, legally valid permission or appropriate ownership rights from the original lecturer or speaker to extract vocal acoustic embeddings, clone their voice characteristics, and synthesize translated derivatives.
            </li>
            <li>
              <strong className="text-zinc-200">Prohibition on Deceptive Impersonation:</strong> You may not use the Platform to generate deceptive, defamatory, political, harassing, or fraudulent audio/video representations of any individual.
            </li>
            <li>
              <strong className="text-zinc-200">Audit Logs:</strong> The Platform records digital attestations (timestamp, user ID, job parameters) whenever voice cloning or derivative dubbing is initiated.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">3.</span> Intellectual Property &amp; Video Rights
          </h2>
          <p>
            You retain all pre-existing copyrights in the lecture videos you submit. You must not import, transcribe, or dub any material that infringes upon third-party intellectual property, trademarks, or trade secrets.
          </p>
          <p>
            If you utilize URL or cloud video import features, you affirm that the content is either owned by you, licensed under appropriate Open Educational Resources (OER / Creative Commons), or used under lawful fair-use educational exemptions.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">4.</span> Automated Machine Translation &amp; Disclaimer of Warranties
          </h2>
          <p>
            Speech recognition (ASR), translation (LLM), and neural voice synthesis are automated algorithmic processes. While Lecture Dubber incorporates duration budgeting, length constraints, and human-in-the-loop review checkpoints, translation errors, dialect nuances, and timing drift can occur.
          </p>
          <p className="text-zinc-400 italic">
            THE SERVICE IS PROVIDED &quot;AS IS&quot; WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO TRANSLATION ACCURACY, FITNESS FOR A PARTICULAR EDUCATIONAL ACCREDITATION, OR NON-INFRINGEMENT.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">5.</span> Watermarking &amp; Provenance Transparency
          </h2>
          <p>
            All video and audio files produced by Lecture Dubber may embed digital metadata tags indicating that the audio stream contains AI-synthesized translation and voice dubbing. You agree not to maliciously tamper with or obscure machine-generated provenance disclosures where required by educational standards.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">6.</span> Termination &amp; Account Suspension
          </h2>
          <p>
            We reserve the right to suspend or terminate access to any user found violating voice consent mandates, generating abusive deepfakes, or executing repeated denial-of-service/SSRF attacks against the ingest pipeline.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400 font-mono text-base">7.</span> Contact &amp; Questions
          </h2>
          <p>
            For legal inquiries regarding these terms, contact{" "}
            <span className="text-indigo-400 font-mono">legal@lecturedubber.local</span>.
          </p>
        </section>
      </div>
    </div>
  );
}
