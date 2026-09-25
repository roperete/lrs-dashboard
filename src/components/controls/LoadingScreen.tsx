import React from 'react';
import { Database } from 'lucide-react';
import { motion, useReducedMotion } from 'motion/react';
import { APP_VERSION } from '../../version';
import { Credits } from '../brand/Credits';
import { cn } from '../../utils/cn';

interface Props {
  key?: React.Key;   // the project has no @types/react, so JSX's key is declared here
  /** What is being loaded, shown under the dots ("Drawing the globe…"). */
  status?: string;
  /** 'page': the whole screen, while the data and then the first view load (it fades out over
   *  the app once the view is drawn). 'area': inside a view, while a view loads later on. */
  mode?: 'page' | 'area';
}

/**
 * The branded loading screen: the database, its version, and its sponsor and developer. It
 * stays up until the first view is actually drawn (the globe's texture takes a while), so
 * the wait shows who made the database rather than an empty frame.
 */
export function LoadingScreen({ status, mode = 'page' }: Props) {
  const still = useReducedMotion();
  const page = mode === 'page';
  return (
    <motion.div
      role="status" aria-live="polite" aria-label={status || 'Loading'}
      initial={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: still ? 0 : 0.45 }}
      className={cn('flex flex-col items-center justify-center bg-slate-950 px-4',
        page ? 'fixed inset-0 z-[3000]' : 'h-full w-full')}
    >
      <motion.div
        initial={still ? false : { opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className={cn('flex flex-col items-center text-center', page ? 'mb-10' : 'mb-6')}
      >
        <div className="p-3 bg-emerald-500 rounded-xl shadow-[0_0_30px_rgba(16,185,129,0.4)] mb-4">
          <Database size={page ? 32 : 24} className="text-slate-950" />
        </div>
        {/* not a heading: the app's own header carries the page title underneath */}
        <p className={cn('font-bold tracking-tight text-white mb-1', page ? 'text-2xl' : 'text-lg')}>
          Lunar Regolith Simulant <span className="text-emerald-500">Database</span>
        </p>
        <p className="text-xs text-slate-400 font-mono uppercase tracking-[0.2em]">Interactive Research Tool</p>
        <p className="mt-2 text-xs font-mono text-emerald-400/80">{APP_VERSION}</p>
      </motion.div>

      <div className={cn('flex flex-col items-center gap-3', page ? 'mb-12' : 'mb-8')}>
        <div className="flex gap-1.5" aria-hidden>
          {[0, 1, 2].map(i => (
            <motion.div key={i} className="w-2 h-2 rounded-full bg-emerald-500"
              animate={still ? { opacity: 0.8 } : { opacity: [0.3, 1, 0.3] }}
              transition={still ? undefined : { duration: 1, repeat: Infinity, delay: i * 0.2 }} />
          ))}
        </div>
        {status && <p className="text-xs text-slate-400">{status}</p>}
      </div>

      <motion.div initial={still ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2, duration: 0.4 }}>
        <Credits variant="splash" />
      </motion.div>
    </motion.div>
  );
}
