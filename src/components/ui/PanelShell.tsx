import React, { useEffect, useState } from 'react';
import { X, Pin, Search, Download, ArrowRightLeft } from 'lucide-react';
import { motion, useDragControls } from 'motion/react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { DragGrip, dragToClose } from './DragToClose';

function cn(...inputs: any[]) { return twMerge(clsx(inputs)); }

/** Wider than a phone: the panel sits on the right; below this it is a bottom sheet. */
function useIsSideSheet() {
  const query = '(min-width: 640px)';
  const [side, setSide] = useState(() => typeof window === 'undefined' || window.matchMedia(query).matches);
  useEffect(() => {
    const m = window.matchMedia(query);
    const on = () => setSide(m.matches);
    m.addEventListener('change', on);
    return () => m.removeEventListener('change', on);
  }, []);
  return side;
}

interface PanelShellProps {
  title: string;
  subtitle?: string;
  pinned?: boolean;
  onClose: () => void;
  onTogglePin?: () => void;
  onSearchSources?: () => void;
  onDownload?: () => void;
  onCompare?: () => void;
  compareActive?: boolean;
  accentColor?: string;
  /** One line under the subtitle, e.g. how many documents name this simulant. */
  headerNote?: React.ReactNode;
  children: React.ReactNode;
}

export function PanelShell({
  title, subtitle, pinned, onClose, onTogglePin, onSearchSources, onDownload,
  onCompare, compareActive, accentColor = 'text-emerald-400', headerNote, children,
}: PanelShellProps) {
  const side = useIsSideSheet();
  const drag = useDragControls();
  const hidden = side ? { x: '100%', y: 0 } : { x: 0, y: '100%' };
  return (
    <motion.div
      initial={hidden} animate={{ x: 0, y: 0 }} exit={hidden}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      {...dragToClose(side ? 'right' : 'down', drag, onClose)}
      className="fixed right-0 bottom-0 h-[70vh] w-full sm:top-0 sm:bottom-auto sm:h-full sm:w-[450px] bg-slate-900/95 backdrop-blur-xl border-l border-t sm:border-t-0 border-slate-800 z-[1000] shadow-2xl rounded-t-2xl sm:rounded-none"
    >
      <DragGrip direction={side ? 'right' : 'down'} controls={drag} onClose={onClose} />
      <div className="h-full overflow-y-auto p-6">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1 min-w-0">
            <h2 className={cn("text-2xl font-bold tracking-tight truncate", accentColor)}>{title}</h2>
            {subtitle && <p className="text-slate-400 font-mono text-sm uppercase tracking-widest">{subtitle}</p>}
            {headerNote}
          </div>
          <div className="flex items-center gap-1 ml-2">
            {onSearchSources && (
              <button onClick={onSearchSources} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white" title="Search Sources">
                <Search size={16} />
              </button>
            )}
            {onDownload && (
              <button onClick={onDownload} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white" title="Download CSV">
                <Download size={16} />
              </button>
            )}
            {onCompare && (
              <button onClick={onCompare}
                className={cn("p-2 rounded-full transition-colors",
                  compareActive ? "bg-blue-500 text-white" : "hover:bg-slate-800 text-slate-400 hover:text-white")}
                title="Compare">
                <ArrowRightLeft size={16} />
              </button>
            )}
            {onTogglePin && (
              <button onClick={onTogglePin}
                className={cn("p-2 rounded-full transition-colors",
                  pinned ? "bg-emerald-500/20 text-emerald-400" : "hover:bg-slate-800 text-slate-400 hover:text-white")}
                title={pinned ? "Unpin" : "Pin"}>
                <Pin size={16} />
              </button>
            )}
            <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
              <X size={20} />
            </button>
          </div>
        </div>
        {children}
      </div>
    </motion.div>
  );
}
