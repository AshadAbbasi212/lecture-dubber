"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowLeft, Send, CheckCircle2, ShieldAlert } from "lucide-react";

export default function TakedownPage() {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    organization: "",
    jobOrUrl: "",
    copyrightWork: "",
    infringementDescription: "",
    goodFaith: false,
    accuracyUnderPerjury: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.goodFaith || !formData.accuracyUnderPerjury) {
      alert("Please affirm the legal compliance declarations before submitting.");
      return;
    }
    setSubmitted(true);
  };

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
          <AlertTriangle className="w-8 h-8 text-rose-400" />
          <h1 className="text-3xl font-extrabold text-white">DMCA &amp; Takedown Requests</h1>
        </div>
        <p className="text-sm text-zinc-400">
          Intellectual Property Infringement &amp; Speaker Voice Rights Notice Procedure
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
            This takedown notice framework is provided as a standard DMCA (17 U.S.C. § 512) and biometric voice rights complaint procedure. Review with local legal counsel prior to commercial launch.
          </p>
        </div>
      </div>

      {submitted ? (
        <div className="bg-zinc-900 border border-emerald-500/30 rounded-3xl p-10 text-center space-y-4">
          <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto" />
          <h2 className="text-2xl font-bold text-white">Takedown Notice Received</h2>
          <p className="text-zinc-400 text-sm max-w-lg mx-auto">
            Your infringement notification regarding <span className="text-white font-medium">{formData.jobOrUrl}</span> has been logged with reference ID <span className="font-mono text-xs text-indigo-400">DMCA-{Date.now().toString(36).toUpperCase()}</span>.
            Our compliance officer will review the claim and promptly disable access to the identified artifacts in accordance with statutory safe harbor guidelines.
          </p>
          <div className="pt-4">
            <Link
              href="/"
              className="inline-block px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-sm font-medium transition-colors"
            >
              Return to Platform
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8">
          <div className="space-y-4 text-sm text-zinc-300">
            <h2 className="text-lg font-bold text-white">Notice Submission Instructions</h2>
            <p>
              Lecture Dubber respects the intellectual property and publicity rights of educators, institutions, and speakers. If you believe your copyrighted video or voice has been reproduced, translated, or cloned without proper authorization, please complete the formal notice form below or send written notice to our designated agent.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6 pt-4 border-t border-zinc-800">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-zinc-300">Your Full Legal Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Dr. Jane Doe"
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-xl px-4 py-2.5 text-sm text-white placeholder-zinc-600 outline-none transition-colors"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-zinc-300">Email Address *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="legal@institution.edu"
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-xl px-4 py-2.5 text-sm text-white placeholder-zinc-600 outline-none transition-colors"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-zinc-300">Organization or Copyright Holder (if applicable)</label>
              <input
                type="text"
                value={formData.organization}
                onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                placeholder="e.g. University Department of Physics / Self"
                className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-xl px-4 py-2.5 text-sm text-white placeholder-zinc-600 outline-none transition-colors"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-zinc-300">Identifier of Dubbed Item on Lecture Dubber (Job ID or Link) *</label>
              <input
                type="text"
                required
                value={formData.jobOrUrl}
                onChange={(e) => setFormData({ ...formData, jobOrUrl: e.target.value })}
                placeholder="e.g. Job ID 8a9f... or original lecture URL"
                className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-xl px-4 py-2.5 text-sm text-white placeholder-zinc-600 outline-none transition-colors"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-zinc-300">Original Copyrighted Work or Speaker Voice Description *</label>
              <textarea
                required
                rows={3}
                value={formData.copyrightWork}
                onChange={(e) => setFormData({ ...formData, copyrightWork: e.target.value })}
                placeholder="Describe the lecture title, publication venue, or speaker identity whose voice/materials were cloned without consent."
                className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-xl p-4 text-sm text-white placeholder-zinc-600 outline-none transition-colors resize-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-zinc-300">Explanation of Infringement / Nature of Claim *</label>
              <textarea
                required
                rows={3}
                value={formData.infringementDescription}
                onChange={(e) => setFormData({ ...formData, infringementDescription: e.target.value })}
                placeholder="State clearly why the use is unauthorized and does not fall under educational fair use exemptions."
                className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-xl p-4 text-sm text-white placeholder-zinc-600 outline-none transition-colors resize-none"
              />
            </div>

            {/* Statutory Declarations */}
            <div className="space-y-4 pt-2 border-t border-zinc-800/80">
              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  required
                  checked={formData.goodFaith}
                  onChange={(e) => setFormData({ ...formData, goodFaith: e.target.checked })}
                  className="mt-1 w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-rose-600 focus:ring-rose-500/20"
                />
                <span className="text-xs text-zinc-300 leading-relaxed group-hover:text-zinc-200">
                  I state under good-faith belief that the use of the copyrighted or vocal material described above is not authorized by the copyright owner, speaker, its agent, or the law.
                </span>
              </label>

              <label className="flex items-start gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  required
                  checked={formData.accuracyUnderPerjury}
                  onChange={(e) => setFormData({ ...formData, accuracyUnderPerjury: e.target.checked })}
                  className="mt-1 w-4 h-4 rounded border-zinc-700 bg-zinc-800 text-rose-600 focus:ring-rose-500/20"
                />
                <span className="text-xs text-zinc-300 leading-relaxed group-hover:text-zinc-200">
                  I state under penalty of perjury that the information in this notification is accurate, and that I am the owner, speaker, or authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.
                </span>
              </label>
            </div>

            <button
              type="submit"
              className="w-full py-3 px-6 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-rose-600/20"
            >
              <Send className="w-4 h-4" />
              Submit Formal Takedown Notice
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
