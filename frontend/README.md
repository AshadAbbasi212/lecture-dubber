# Lecture Dubber - Web Application Frontend

Modern, high-performance web application built with **Next.js 16 (App Router)**, **React 19**, **TypeScript**, and **Tailwind CSS**.

---

## Key Features

- **Live Pipeline Streaming**: Real-time Server-Sent Events (SSE) stepper showing stage execution progress, time estimates, and stage status without manual polling.
- **Resumable Chunk Uploads**: Upload lectures of any size using client-side 5 MB chunk slicing with automatic offset resumption on network interruption.
- **Interactive Segment Reviewer**: Side-by-side bilingual review screen with RTL Urdu typography, inline segment editing, auto-save, and one-click synthesis approval.
- **Audition Voice Gallery**: Interactive studio gallery featuring 24 authentic neural voice samples across all supported languages and genders (Male & Female).
- **Result Video & Audio Center**: HTML5 media player previewing dubbed video with multi-language subtitle tracks (.srt/.vtt), audio-only MP3 exports, and secure short-lived download links.
- **Legal Compliance Suite**: Terms of Service, Privacy Policy, and DMCA / Biometric takedown notice submission portals.

---

## Tech Stack

- **Framework**: Next.js 16 (Turbopack) with App Router
- **UI & State**: React 19, Lucide React Icons
- **Styling**: Tailwind CSS with custom RTL Urdu typography classes
- **Type Safety**: TypeScript 5.x

---

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Production Build & Static Optimization
```bash
npm run build
npm start
```
