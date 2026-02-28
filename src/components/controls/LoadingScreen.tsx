import React from 'react';
import { Database } from 'lucide-react';
import { motion } from 'motion/react';

export function LoadingScreen() {
  return (
    <div className="h-dvh w-screen bg-slate-950 flex flex-col items-center justify-center">
      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col items-center mb-12"
      >
        <div className="p-3 bg-emerald-500 rounded-xl shadow-[0_0_30px_rgba(16,185,129,0.4)] mb-4">
          <Database size={32} className="text-slate-950" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white mb-1">
          Lunar Regolith Simulant <span className="text-emerald-500">Database</span>
        </h1>
        <p className="text-xs text-slate-500 font-mono uppercase tracking-[0.2em]">
          Interactive Research Tool
        </p>
      </motion.div>

      {/* Loading indicator */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className="mb-16"
      >
        <div className="flex gap-1.5">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-emerald-500"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
            />
          ))}
        </div>
      </motion.div>

      {/* Sponsors */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        className="flex flex-col items-center gap-6"
      >
        <div className="flex items-center gap-8">
          {/* Sponsored by CNES */}
          <div className="flex flex-col items-center gap-2">
            <span className="text-[10px] text-slate-600 uppercase tracking-wider">Sponsored by</span>
            <img src={import.meta.env.BASE_URL + 'assets/cnes-logo.png'} alt="CNES" className="h-12 w-auto object-contain" />
          </div>

          <div className="w-px h-12 bg-slate-800" />

          {/* Developed by The Spring Institute */}
          <div className="flex flex-col items-center gap-2">
            <span className="text-[10px] text-slate-600 uppercase tracking-wider">Developed by</span>
            <img src={import.meta.env.BASE_URL + 'assets/spring-logo.png'} alt="The Spring Institute" className="h-12 w-auto object-contain" />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
