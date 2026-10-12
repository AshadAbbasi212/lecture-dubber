"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import { Play, Pause, Volume2, Check, Sparkles, User, GraduationCap, Globe2, Radio, UserCheck } from "lucide-react";

export interface VoiceItem {
  id: string;
  name: string;
  lang: string;
  langName: string;
  gender: "Male" | "Female";
  accent: string;
  role: string;
  description: string;
  color: string;
  gradient: string;
  badge: string;
}

export const VOICES_ROSTER: VoiceItem[] = [
  // --- English (7 Voices: 5 Male, 2 Female) ---
  {
    id: "ryan",
    name: "Ryan",
    lang: "en",
    langName: "English",
    gender: "Male",
    accent: "American (US)",
    role: "Scholar Baritone",
    description: "Deep, resonant scholar baritone with gravitas. Ideal for classic lectures, philosophy, and bayans.",
    color: "#6366f1",
    gradient: "from-indigo-500 to-blue-600",
    badge: "Scholar Choice"
  },
  {
    id: "amy",
    name: "Amy",
    lang: "en",
    langName: "English",
    gender: "Female",
    accent: "American (US)",
    role: "Academic Narrator",
    description: "Warm, natural, crystal-clear modern lecture enunciation with approachable human cadence.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Most Natural"
  },
  {
    id: "alan",
    name: "Alan",
    lang: "en",
    langName: "English",
    gender: "Male",
    accent: "British (UK)",
    role: "Classical Professor",
    description: "Refined British academic tone with crisp scholarly diction and articulate pacing.",
    color: "#06b6d4",
    gradient: "from-cyan-500 to-teal-600",
    badge: "UK Academic"
  },
  {
    id: "lessac",
    name: "Lessac",
    lang: "en",
    langName: "English",
    gender: "Female",
    accent: "American (US)",
    role: "Studio Documentary",
    description: "Smooth, articulate broadcast documentary narration with pristine studio audio clarity.",
    color: "#8b5cf6",
    gradient: "from-purple-500 to-indigo-600",
    badge: "Documentary"
  },
  {
    id: "kusal",
    name: "Kusal",
    lang: "en",
    langName: "English",
    gender: "Male",
    accent: "American (US)",
    role: "Seminar Lecturer",
    description: "Warm, engaging conversational academic male timbre with balanced tempo.",
    color: "#10b981",
    gradient: "from-emerald-500 to-green-600",
    badge: "Clear & Calm"
  },
  {
    id: "reza",
    name: "Reza",
    lang: "en",
    langName: "English",
    gender: "Male",
    accent: "American (US)",
    role: "Expressive Storyteller",
    description: "Dynamic, evocative vocal range and inflection. Excellent for historical narrative lectures.",
    color: "#f59e0b",
    gradient: "from-amber-500 to-orange-600",
    badge: "Expressive"
  },
  {
    id: "l2arctic",
    name: "L2 Arctic",
    lang: "en",
    langName: "English",
    gender: "Male",
    accent: "International",
    role: "Global English",
    description: "Balanced international English resonance, natural and relatable for worldwide students.",
    color: "#0ea5e9",
    gradient: "from-sky-500 to-blue-600",
    badge: "International"
  },

  // --- Arabic (Male & Female) ---
  {
    id: "kareem",
    name: "Kareem (كريم)",
    lang: "ar",
    langName: "Arabic",
    gender: "Male",
    accent: "Modern Standard Arabic",
    role: "Scholar Baritone",
    description: "Deep, authentic classical Arabic lecture resonance with dignified scholarly gravitas.",
    color: "#10b981",
    gradient: "from-emerald-500 to-teal-600",
    badge: "Scholar Baritone"
  },
  {
    id: "maryam",
    name: "Maryam (مريم)",
    lang: "ar",
    langName: "Arabic",
    gender: "Female",
    accent: "Modern Standard Arabic",
    role: "Academic Lecturer",
    description: "Clear, elegant classical Arabic lecture enunciation with natural academic rhythm and warm cadence.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Academic Female"
  },

  // --- Chinese (Mandarin Male & Female) ---
  {
    id: "huayan",
    name: "Huayan (华研)",
    lang: "zh",
    langName: "Chinese",
    gender: "Female",
    accent: "Standard Mandarin",
    role: "Academic Lecturer",
    description: "Standard Putonghua enunciation with crystal-clear scholarly tone and natural rhythm.",
    color: "#ef4444",
    gradient: "from-red-500 to-rose-600",
    badge: "Putonghua Studio"
  },
  {
    id: "chaowen",
    name: "Chaowen (超文)",
    lang: "zh",
    langName: "Chinese",
    gender: "Male",
    accent: "Standard Mandarin",
    role: "University Professor",
    description: "Authoritative, dignified Putonghua professor tone with balanced educational tempo.",
    color: "#3b82f6",
    gradient: "from-blue-500 to-cyan-600",
    badge: "University Professor"
  },

  // --- Russian (Male & Female) ---
  {
    id: "denis",
    name: "Denis (Денис)",
    lang: "ru",
    langName: "Russian",
    gender: "Male",
    accent: "Standard Russian",
    role: "Professor Baritone",
    description: "Authoritative, resonant academic lecturing tone with precise scientific clarity.",
    color: "#3b82f6",
    gradient: "from-blue-500 to-cyan-600",
    badge: "Professor Baritone"
  },
  {
    id: "irina",
    name: "Irina (Ирина)",
    lang: "ru",
    langName: "Russian",
    gender: "Female",
    accent: "Standard Russian",
    role: "Academic Narrator",
    description: "Warm, expressive university lecture enunciation with fluid human cadence.",
    color: "#a855f7",
    gradient: "from-purple-500 to-pink-600",
    badge: "Academic Narrator"
  },

  // --- Spanish (Male & Female) ---
  {
    id: "dave",
    name: "Dave (David)",
    lang: "es",
    langName: "Spanish",
    gender: "Male",
    accent: "Castilian (Spain)",
    role: "University Professor",
    description: "Articulate European Spanish academic delivery with balanced pace and natural warmth.",
    color: "#f97316",
    gradient: "from-orange-500 to-amber-600",
    badge: "Castilian Professor"
  },
  {
    id: "sharvard",
    name: "Elena (Sharvard)",
    lang: "es",
    langName: "Spanish",
    gender: "Female",
    accent: "Castilian (Spain)",
    role: "Academic Narrator",
    description: "Refined European Spanish enunciation with crystal-clear lecture inflection and smooth cadence.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Castilian Academic"
  },

  // --- French (Male & Female) ---
  {
    id: "gilles",
    name: "Gilles",
    lang: "fr",
    langName: "French",
    gender: "Male",
    accent: "Parisian Standard",
    role: "University Professor",
    description: "Rich, resonant Parisian academic timbre with distinguished scientific clarity.",
    color: "#3b82f6",
    gradient: "from-blue-500 to-indigo-600",
    badge: "Sorbonne Professor"
  },
  {
    id: "siwis",
    name: "Siwis (Céline)",
    lang: "fr",
    langName: "French",
    gender: "Female",
    accent: "Parisian Standard",
    role: "Academic Lecturer",
    description: "Articulate, elegant European French lecture enunciation with pristine vocal timbre.",
    color: "#6366f1",
    gradient: "from-indigo-500 to-violet-600",
    badge: "Parisian Academic"
  },

  // --- German (Male & Female) ---
  {
    id: "thorsten",
    name: "Thorsten",
    lang: "de",
    langName: "German",
    gender: "Male",
    accent: "Standard German",
    role: "Professor Baritone",
    description: "Warm, authoritative German baritone with precise academic diction and clarity.",
    color: "#eab308",
    gradient: "from-yellow-500 to-amber-600",
    badge: "Professor Baritone"
  },
  {
    id: "kerstin",
    name: "Kerstin",
    lang: "de",
    langName: "German",
    gender: "Female",
    accent: "Standard German",
    role: "University Lecturer",
    description: "Crystal-clear, methodical German lecture delivery with natural professional cadence.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "University Lecturer"
  },

  // --- Hindi (Male & Female) ---
  {
    id: "pratham",
    name: "Pratham (प्रथम)",
    lang: "hi",
    langName: "Hindi",
    gender: "Male",
    accent: "Standard Hindi",
    role: "University Lecturer",
    description: "Crisp, respectful academic pacing with clear pronunciation for educational topics.",
    color: "#f97316",
    gradient: "from-orange-500 to-rose-600",
    badge: "Standard Hindi"
  },
  {
    id: "priyamvada",
    name: "Priyamvada (प्रियंवदा)",
    lang: "hi",
    langName: "Hindi",
    gender: "Female",
    accent: "Standard Hindi",
    role: "Academic Narrator",
    description: "Warm, articulate Hindi enunciation with respectful scholarly tone and engaging rhythm.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Academic Female"
  },

  // --- Portuguese (Male & Female) ---
  {
    id: "faber",
    name: "Faber",
    lang: "pt",
    langName: "Portuguese",
    gender: "Male",
    accent: "Brazilian Portuguese",
    role: "Academic Lecturer",
    description: "Smooth, engaging Brazilian university lecturing tone with natural rhythm.",
    color: "#10b981",
    gradient: "from-emerald-500 to-green-600",
    badge: "Brazilian Academic"
  },
  {
    id: "larissa",
    name: "Larissa",
    lang: "pt",
    langName: "Portuguese",
    gender: "Female",
    accent: "Brazilian Portuguese",
    role: "Academic Narrator",
    description: "Vibrant, natural Brazilian academic delivery with articulate, friendly clarity.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Academic Female"
  },

  // --- Italian (Male & Female) ---
  {
    id: "riccardo",
    name: "Riccardo",
    lang: "it",
    langName: "Italian",
    gender: "Male",
    accent: "Standard Italian",
    role: "University Professor",
    description: "Warm, expressive Italian professor cadence with crisp articulation and scholarly gravitas.",
    color: "#3b82f6",
    gradient: "from-blue-500 to-cyan-600",
    badge: "Italian Professor"
  },
  {
    id: "paola",
    name: "Paola",
    lang: "it",
    langName: "Italian",
    gender: "Female",
    accent: "Standard Italian",
    role: "Academic Professor",
    description: "Melodious, articulate Italian lecture cadence with natural expressive inflection.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Florentine Academic"
  },

  // --- Turkish (Male & Female) ---
  {
    id: "dfki",
    name: "Kerem (DFKI)",
    lang: "tr",
    langName: "Turkish",
    gender: "Male",
    accent: "Istanbul Turkish",
    role: "University Lecturer",
    description: "Crisp, formal Turkish academic diction ideal for higher education seminars.",
    color: "#06b6d4",
    gradient: "from-cyan-500 to-blue-600",
    badge: "Istanbul Academic"
  },
  {
    id: "leyla",
    name: "Leyla",
    lang: "tr",
    langName: "Turkish",
    gender: "Female",
    accent: "Istanbul Turkish",
    role: "Academic Narrator",
    description: "Smooth, natural Istanbul lecture delivery with clear educational modulation.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Academic Female"
  },

  // --- Urdu (Male & Female) ---
  {
    id: "tariq",
    name: "Tariq (طارق)",
    lang: "ur",
    langName: "Urdu",
    gender: "Male",
    accent: "Standard Urdu / Bayan",
    role: "Bayan Scholar Baritone",
    description: "Deep scholarly resonance with authentic educational pacing and speaker timbre transfer.",
    color: "#14b8a6",
    gradient: "from-teal-500 to-emerald-600",
    badge: "Bayan Scholar"
  },
  {
    id: "ayesha",
    name: "Ayesha (عائشہ)",
    lang: "ur",
    langName: "Urdu",
    gender: "Female",
    accent: "Standard Urdu / Bayan",
    role: "Academic Lecturer",
    description: "Clear, dignified Urdu academic enunciation tailored for educational lectures and presentations.",
    color: "#ec4899",
    gradient: "from-pink-500 to-rose-600",
    badge: "Academic Female"
  }
];

interface VoiceGalleryProps {
  selectedVoice?: string;
  onSelectVoice?: (voiceId: string) => void;
  targetLang?: string;
}

export default function VoiceGallery({ 
  selectedVoice = "ryan", 
  onSelectVoice = () => {}, 
  targetLang 
}: VoiceGalleryProps) {
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [playbackTime, setPlaybackTime] = useState<number>(0);
  const [activeLangFilter, setActiveLangFilter] = useState<string>(targetLang || "all");
  const [activeGenderFilter, setActiveGenderFilter] = useState<"all" | "Male" | "Female">("all");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Sync active language filter when targetLang changes from parent
  useEffect(() => {
    if (targetLang) {
      setActiveLangFilter(targetLang);
    }
  }, [targetLang]);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const handlePlay = (voiceId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (playingVoice === voiceId) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setPlayingVoice(null);
      setPlaybackTime(0);
      return;
    }

    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(`/voices/${voiceId}.wav`);
    audioRef.current = audio;
    setPlayingVoice(voiceId);
    setPlaybackTime(0);

    audio.ontimeupdate = () => {
      setPlaybackTime(Math.round(audio.currentTime));
    };

    audio.onended = () => {
      setPlayingVoice(null);
      setPlaybackTime(0);
    };

    audio.onerror = () => {
      setPlayingVoice(null);
      setPlaybackTime(0);
    };

    audio.play().catch(() => {
      setPlayingVoice(null);
    });
  };

  const filteredVoices = useMemo(() => {
    return VOICES_ROSTER.filter((v) => {
      const matchLang = activeLangFilter === "all" || v.lang === activeLangFilter;
      const matchGender = activeGenderFilter === "all" || v.gender === activeGenderFilter;
      return matchLang && matchGender;
    });
  }, [activeLangFilter, activeGenderFilter]);

  const uniqueLangs = useMemo(() => {
    const map = new Map<string, string>();
    VOICES_ROSTER.forEach((v) => {
      if (!map.has(v.lang)) {
        map.set(v.lang, v.langName);
      }
    });
    return Array.from(map.entries());
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <label className="block text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
            Audition & Select Dubbing Voice
          </label>
          <p className="text-xs text-slate-400 mt-0.5">
            Select an authentic neural voice. Click <span className="text-indigo-400 font-medium">10s Audition</span> to preview natural human cadence.
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-mono text-indigo-300 shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>{filteredVoices.length} Voices Available ({VOICES_ROSTER.length} Total)</span>
        </div>
      </div>

      {/* Filter Row: Gender Filter + Language Quick-Filter Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-900/60 p-2.5 rounded-2xl border border-slate-800">
        {/* Gender Tabs */}
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">Gender:</span>
          <button
            type="button"
            onClick={() => setActiveGenderFilter("all")}
            className={`px-3 py-1 rounded-xl text-xs font-medium transition-all ${
              activeGenderFilter === "all"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                : "bg-slate-800 text-slate-300 hover:text-white"
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => setActiveGenderFilter("Male")}
            className={`px-3 py-1 rounded-xl text-xs font-medium transition-all flex items-center gap-1 ${
              activeGenderFilter === "Male"
                ? "bg-blue-600 text-white shadow-md shadow-blue-600/30 font-semibold"
                : "bg-slate-800 text-slate-300 hover:text-white"
            }`}
          >
            <span>👨</span>
            <span>Male</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveGenderFilter("Female")}
            className={`px-3 py-1 rounded-xl text-xs font-medium transition-all flex items-center gap-1 ${
              activeGenderFilter === "Female"
                ? "bg-pink-600 text-white shadow-md shadow-pink-600/30 font-semibold"
                : "bg-slate-800 text-slate-300 hover:text-white"
            }`}
          >
            <span>👩</span>
            <span>Female</span>
          </button>
        </div>

        {/* Language Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 scrollbar-thin">
          <button
            type="button"
            onClick={() => setActiveLangFilter("all")}
            className={`px-3 py-1 rounded-xl text-xs font-medium transition-all shrink-0 ${
              activeLangFilter === "all"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            All Langs
          </button>
          {uniqueLangs.map(([code, name]) => {
            const isSelected = activeLangFilter === code;
            return (
              <button
                key={code}
                type="button"
                onClick={() => setActiveLangFilter(code)}
                className={`px-2.5 py-1 rounded-xl text-xs font-medium transition-all flex items-center gap-1 shrink-0 ${
                  isSelected
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <span>{name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3D Voice Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 perspective-1000">
        {filteredVoices.map((v) => {
          const isSelected = selectedVoice === v.id;
          const isPlayingThis = playingVoice === v.id;

          return (
            <div
              key={`${v.lang}-${v.id}`}
              onClick={() => onSelectVoice(v.id)}
              className={`card-3d relative p-4 rounded-2xl border cursor-pointer transition-all duration-300 text-left group overflow-hidden ${
                isSelected
                  ? "bg-gradient-to-br from-indigo-950/70 via-slate-900/90 to-slate-950 border-indigo-500/80 shadow-xl shadow-indigo-500/10 ring-1 ring-indigo-500/50"
                  : "bg-slate-900/50 hover:bg-slate-900/80 border-slate-800/80 hover:border-slate-700"
              }`}
            >
              {/* Dynamic Equalizer Glow on playback */}
              {isPlayingThis && (
                <div className="absolute inset-0 bg-indigo-500/5 animate-pulse pointer-events-none rounded-2xl" />
              )}

              {/* Top Row: Language, Gender Badge, & Role Badge */}
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700/80 text-slate-300">
                    {v.langName}
                  </span>
                  
                  {/* Distinct Gender Badge */}
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border ${
                    v.gender === "Female"
                      ? "bg-pink-500/15 border-pink-500/30 text-pink-300"
                      : "bg-blue-500/15 border-blue-500/30 text-blue-300"
                  }`}>
                    <span>{v.gender === "Female" ? "👩" : "👨"}</span>
                    <span>{v.gender}</span>
                  </span>

                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                    {v.badge}
                  </span>
                </div>

                {isSelected ? (
                  <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/50">
                    <Check className="w-3 h-3 stroke-[2.5]" />
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border border-slate-700 group-hover:border-slate-500 flex items-center justify-center shrink-0" />
                )}
              </div>

              {/* Voice Name & Role */}
              <div className="space-y-0.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                    {v.name}
                  </h3>
                  <span className="text-[11px] text-slate-400">
                    {v.accent}
                  </span>
                </div>
                <div className="text-xs font-medium text-indigo-400 flex items-center gap-1">
                  <GraduationCap className="w-3.5 h-3.5" />
                  <span>{v.role}</span>
                </div>
              </div>

              {/* Description */}
              <p className="text-[11px] text-slate-400 mt-2 leading-relaxed line-clamp-2">
                {v.description}
              </p>

              {/* Bottom Audition Bar */}
              <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <button
                  type="button"
                  onClick={(e) => handlePlay(v.id, e)}
                  className={`btn-3d px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                    isPlayingThis
                      ? "bg-rose-600 text-white shadow-lg shadow-rose-600/30 scale-[1.02]"
                      : "bg-slate-800/90 hover:bg-indigo-600 text-slate-200 hover:text-white border border-slate-700 hover:border-transparent"
                  }`}
                >
                  {isPlayingThis ? (
                    <>
                      <Pause className="w-3.5 h-3.5 fill-current" />
                      <span>Stop ({playbackTime}s)</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current text-indigo-400 group-hover:text-white" />
                      <span>10s Audition</span>
                    </>
                  )}
                </button>

                {/* Animated Soundwave EQ Bars */}
                {isPlayingThis ? (
                  <div className="flex items-center gap-0.5 h-4 px-2 py-0.5 rounded-lg bg-indigo-950/60 border border-indigo-500/30">
                    <span className="soundwave-bar h-2 w-0.5 bg-indigo-400 animate-pulse" />
                    <span className="soundwave-bar h-3.5 w-0.5 bg-indigo-400 animate-pulse delay-75" />
                    <span className="soundwave-bar h-2.5 w-0.5 bg-indigo-400 animate-pulse delay-150" />
                    <span className="soundwave-bar h-4 w-0.5 bg-indigo-400 animate-pulse delay-100" />
                    <span className="soundwave-bar h-1.5 w-0.5 bg-indigo-400 animate-pulse delay-200" />
                  </div>
                ) : (
                  <span className="text-[10px] text-slate-500 font-mono">
                    24kHz Studio WAV
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
