import React from 'react';
import { Globe as GlobeIcon } from 'lucide-react';
import { motion } from 'motion/react';

export function LoadingScreen() {
  return (
    <div className="h-screen w-screen bg-slate-950 flex flex-col items-center justify-center text-emerald-500 font-mono">
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} className="mb-4">
        <GlobeIcon size={48} />
      </motion.div>
      <p className="text-xl tracking-widest animate-pulse">INITIALIZING SPATIAL DATABASE...</p>
    </div>
  );
}
