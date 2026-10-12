"use client";

import React, { useEffect, useRef, useState } from "react";
import { Play, RotateCcw, Volume2, VolumeX, Trophy, Sparkles, CheckCircle2 } from "lucide-react";

interface DubberArcadeProps {
  jobStage?: string;
  jobProgress?: number;
  isJobCompleted?: boolean;
  onViewResult?: () => void;
}

export default function DubberArcade({
  jobStage = "Processing",
  jobProgress = 0,
  isJobCompleted = false,
  onViewResult
}: DubberArcadeProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isGameOver, setIsGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [highScore, setHighScore] = useState(0);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Audio Context for 8-bit retro sound effects
  const audioCtxRef = useRef<AudioContext | null>(null);

  const playBeep = (freq: number, type: OscillatorType = "sine", duration: number = 0.1) => {
    if (!soundEnabled) return;
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") ctx.resume();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch {
      // Audio not permitted or unsupported
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem("dubber_arcade_high");
    if (saved) setHighScore(parseInt(saved, 10) || 0);
  }, []);

  // Game Engine State
  const gameStateRef = useRef({
    playerY: 150,
    playerTargetY: 150,
    playerX: 60,
    speed: 3.5,
    obstacles: [] as Array<{ x: number; y: number; w: number; h: number; type: "spike" | "crystal" | "star" }>,
    wavePhase: 0,
    particles: [] as Array<{ x: number; y: number; vx: number; vy: number; life: number; color: string }>,
    score: 0,
    keys: { up: false, down: false }
  });

  const startGame = () => {
    setIsPlaying(true);
    setIsGameOver(false);
    setScore(0);
    gameStateRef.current = {
      playerY: 150,
      playerTargetY: 150,
      playerX: 60,
      speed: 3.8,
      obstacles: [],
      wavePhase: 0,
      particles: [],
      score: 0,
      keys: { up: false, down: false }
    };
    playBeep(440, "square", 0.15);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (["ArrowUp", "KeyW"].includes(e.code)) {
        gameStateRef.current.keys.up = true;
        e.preventDefault();
      }
      if (["ArrowDown", "KeyS"].includes(e.code)) {
        gameStateRef.current.keys.down = true;
        e.preventDefault();
      }
      if (e.code === "Space" && !isPlaying) {
        startGame();
        e.preventDefault();
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (["ArrowUp", "KeyW"].includes(e.code)) gameStateRef.current.keys.up = false;
      if (["ArrowDown", "KeyS"].includes(e.code)) gameStateRef.current.keys.down = false;
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [isPlaying]);

  // Main Loop
  useEffect(() => {
    if (!isPlaying) return;
    let animId: number;
    let frame = 0;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const game = gameStateRef.current;

    const spawnObstacle = () => {
      const types: Array<"spike" | "crystal" | "star"> = ["spike", "spike", "crystal", "star"];
      const chosen = types[Math.floor(Math.random() * types.length)];
      const y = Math.random() * (canvas.height - 60) + 30;
      game.obstacles.push({
        x: canvas.width + 20,
        y,
        w: chosen === "spike" ? 22 : 18,
        h: chosen === "spike" ? 22 : 18,
        type: chosen
      });
    };

    const loop = () => {
      frame++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 1. Draw Cyber Sound Wave Background
      game.wavePhase += 0.04;
      ctx.strokeStyle = "rgba(99, 102, 241, 0.25)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x += 10) {
        const y = canvas.height / 2 + Math.sin(x * 0.02 + game.wavePhase) * 40 * Math.sin(frame * 0.01);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Subtle Equalizer Spectrum Lines
      ctx.fillStyle = "rgba(6, 182, 212, 0.08)";
      for (let i = 0; i < canvas.width; i += 16) {
        const barH = 15 + Math.sin(i * 0.05 + game.wavePhase) * 20;
        ctx.fillRect(i, canvas.height - barH, 6, barH);
      }

      // 2. Update Player Position
      if (game.keys.up) game.playerY -= 5.5;
      if (game.keys.down) game.playerY += 5.5;
      // Smooth interpolation to target
      game.playerY += (game.playerTargetY - game.playerY) * 0.12;
      game.playerY = Math.max(20, Math.min(canvas.height - 20, game.playerY));

      // Player Particle Trail
      if (frame % 2 === 0) {
        game.particles.push({
          x: game.playerX - 6,
          y: game.playerY + (Math.random() * 6 - 3),
          vx: -(Math.random() * 2 + 1),
          vy: (Math.random() * 2 - 1),
          life: 1.0,
          color: frame % 4 === 0 ? "#06b6d4" : "#818cf8"
        });
      }

      // 3. Update & Draw Particles
      for (let i = game.particles.length - 1; i >= 0; i--) {
        const p = game.particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.035;
        if (p.life <= 0) {
          game.particles.splice(i, 1);
          continue;
        }
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.life;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2.5 * p.life, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0;
      }

      // 4. Draw Player (Futuristic Neon Sound Cursor)
      ctx.save();
      ctx.translate(game.playerX, game.playerY);
      ctx.shadowColor = "#818cf8";
      ctx.shadowBlur = 15;
      // Cursor Body
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.moveTo(14, 0);
      ctx.lineTo(-10, -9);
      ctx.lineTo(-4, 0);
      ctx.lineTo(-10, 9);
      ctx.closePath();
      ctx.fill();

      // Core Engine Pulse
      ctx.fillStyle = "#06b6d4";
      ctx.beginPath();
      ctx.arc(0, 0, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // 5. Spawn & Update Obstacles/Items
      if (frame % 45 === 0) {
        spawnObstacle();
        game.speed = Math.min(7.0, game.speed + 0.03);
      }

      for (let i = game.obstacles.length - 1; i >= 0; i--) {
        const obs = game.obstacles[i];
        obs.x -= game.speed;

        // Collision Check
        const dist = Math.hypot(obs.x - game.playerX, obs.y - game.playerY);

        if (obs.type === "spike") {
          // Draw Red Noise Glitch
          ctx.save();
          ctx.fillStyle = "#f43f5e";
          ctx.shadowColor = "#f43f5e";
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.moveTo(obs.x, obs.y - 10);
          ctx.lineTo(obs.x + 10, obs.y + 10);
          ctx.lineTo(obs.x - 10, obs.y + 10);
          ctx.closePath();
          ctx.fill();
          ctx.restore();

          if (dist < 18) {
            // Collision with spike -> Game Over
            playBeep(180, "sawtooth", 0.3);
            setIsGameOver(true);
            setIsPlaying(false);
            if (game.score > highScore) {
              setHighScore(game.score);
              localStorage.setItem("dubber_arcade_high", game.score.toString());
            }
            return;
          }
        } else if (obs.type === "crystal") {
          // Draw Cyan Phoneme Note
          ctx.save();
          ctx.fillStyle = "#06b6d4";
          ctx.shadowColor = "#06b6d4";
          ctx.shadowBlur = 10;
          ctx.beginPath();
          ctx.arc(obs.x, obs.y, 7, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = "#ffffff";
          ctx.beginPath();
          ctx.arc(obs.x, obs.y, 3, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          if (dist < 18) {
            // Pick up crystal (+15 pts)
            playBeep(660, "sine", 0.08);
            game.score += 15;
            setScore(game.score);
            game.obstacles.splice(i, 1);
            continue;
          }
        } else if (obs.type === "star") {
          // Draw Gold Sync Star
          ctx.save();
          ctx.fillStyle = "#f59e0b";
          ctx.shadowColor = "#f59e0b";
          ctx.shadowBlur = 14;
          ctx.beginPath();
          ctx.arc(obs.x, obs.y, 8, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          if (dist < 20) {
            // Pick up star (+35 pts)
            playBeep(880, "triangle", 0.12);
            game.score += 35;
            setScore(game.score);
            game.obstacles.splice(i, 1);
            continue;
          }
        }

        // Remove off-screen
        if (obs.x < -30) {
          game.obstacles.splice(i, 1);
          game.score += 2;
          setScore(game.score);
        }
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying, highScore, soundEnabled]);

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !isPlaying) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const y = ((e.clientY - rect.top) / rect.height) * canvasRef.current.height;
    gameStateRef.current.playerTargetY = y;
  };

  const handleCanvasTouchMove = (e: React.TouchEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !isPlaying) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const touch = e.touches[0];
    const y = ((touch.clientY - rect.top) / rect.height) * canvasRef.current.height;
    gameStateRef.current.playerTargetY = y;
  };

  return (
    <div className="relative rounded-2xl overflow-hidden border border-indigo-500/30 bg-slate-950/90 shadow-2xl shadow-indigo-950/60 perspective-1000">
      {/* Top Game Bar & Real-Time Job Progress Tracker */}
      <div className="px-4 py-2.5 bg-slate-900/90 border-b border-indigo-500/20 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
          </span>
          <span className="text-xs font-bold text-white tracking-wide uppercase flex items-center gap-1.5">
            <span>🎮 SoundWave Surfer</span>
            <span className="text-[10px] text-indigo-400 font-mono font-normal">
              (Play while dubbing renders!)
            </span>
          </span>
        </div>

        {/* Live Dubbing Status Pill */}
        <div className="flex items-center gap-2 bg-indigo-950/60 border border-indigo-500/30 px-3 py-1 rounded-full text-xs">
          <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-spin" />
          <span className="text-slate-300 font-medium">Stage:</span>
          <span className="text-indigo-300 font-semibold capitalize">{jobStage}</span>
          <span className="text-slate-500">•</span>
          <span className="text-emerald-400 font-bold">{jobProgress}%</span>
        </div>

        {/* Controls & Scores */}
        <div className="flex items-center gap-3">
          <div className="text-xs text-slate-300 font-mono flex items-center gap-1.5">
            <Trophy className="w-3.5 h-3.5 text-amber-400" />
            <span>Score: <strong className="text-cyan-300">{score}</strong></span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">Best: {highScore}</span>
          </div>

          <button
            type="button"
            onClick={() => setSoundEnabled(!soundEnabled)}
            title={soundEnabled ? "Mute Game Sound" : "Enable Game Sound"}
            className="p-1 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            {soundEnabled ? <Volume2 className="w-3.5 h-3.5 text-cyan-400" /> : <VolumeX className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Game Canvas Container */}
      <div className="relative w-full h-[240px] bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center overflow-hidden">
        <canvas
          ref={canvasRef}
          width={640}
          height={240}
          onMouseMove={handleCanvasMouseMove}
          onTouchMove={handleCanvasTouchMove}
          className="w-full h-full cursor-crosshair block"
        />

        {/* Start / Idle Screen Overlay */}
        {!isPlaying && !isGameOver && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xs flex flex-col items-center justify-center p-6 text-center space-y-3 z-10">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-6 h-6 text-indigo-400 animate-pulse" />
            </div>
            <div>
              <h4 className="text-base font-bold text-white">Surf the Audio Wave!</h4>
              <p className="text-xs text-slate-400 max-w-sm mt-0.5">
                Steer with Mouse, Arrow Keys, or W/S. Collect <span className="text-cyan-400 font-medium">Phonemes (+15)</span> and dodge <span className="text-rose-400 font-medium">Noise Spikes</span> while your video processes!
              </p>
            </div>
            <button
              type="button"
              onClick={startGame}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-400 hover:to-cyan-400 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-indigo-500/25 flex items-center gap-2 btn-3d"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Start Surfing Now
            </button>
          </div>
        )}

        {/* Game Over Screen Overlay */}
        {isGameOver && (
          <div className="absolute inset-0 bg-slate-950/85 backdrop-blur-xs flex flex-col items-center justify-center p-6 text-center space-y-3 z-10">
            <div className="text-rose-400 text-xs font-mono font-bold uppercase tracking-widest bg-rose-500/10 px-3 py-1 rounded-full border border-rose-500/30">
              Noise Spike Collision!
            </div>
            <h4 className="text-lg font-extrabold text-white">Final Score: <span className="text-cyan-400">{score}</span></h4>
            <button
              type="button"
              onClick={startGame}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 btn-3d"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Play Again
            </button>
          </div>
        )}

        {/* Victory Screen if Job Finishes */}
        {isJobCompleted && (
          <div className="absolute inset-0 bg-emerald-950/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center space-y-3 z-20">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-400/50 flex items-center justify-center text-emerald-400 shadow-xl shadow-emerald-500/30">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <h4 className="text-lg font-black text-white">Your Dubbed Video is Ready!</h4>
              <p className="text-xs text-emerald-200 mt-0.5">
                The entire lecture has been translated, voiced, and muxed.
              </p>
            </div>
            {onViewResult && (
              <button
                type="button"
                onClick={onViewResult}
                className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs uppercase tracking-wider shadow-lg shadow-emerald-500/30 btn-3d"
              >
                Watch Final Dubbed Video →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
