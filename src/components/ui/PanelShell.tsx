import React, { useEffect, useState } from 'react';
import { X, Search, Download, ArrowRightLeft } from 'lucide-react';
import { motion, useDragControls } from 'motion/react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { DragGrip, dragToClose } from './DragToClose';
import { ErrorBoundary } from './ErrorBoundary';

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
  onClose: () => void;
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
  title, subtitle, onClose, onSearchSources, onDownload,
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
      className="fixed right-0 bottom-0 h-[70vh] w-full sm:top-14 sm:bottom-0 sm:h-auto sm:w-[450px] bg-slate-900/95 backdrop-blur-xl border-l border-t sm:border-t-0 border-slate-800 z-[1000] shadow-2xl rounded-t-2xl sm:rounded-none"
    >
      <DragGrip direction={side ? 'right' : 'down'} controls={drag} onClose={onClose} />
      <div className="h-full overflow-y-auto p-6">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1 min-w-0">
            <h2 className={cn("text-2xl font-bold tracking-tight truncate", accentColor)}>{title}</h2>
            {subtitle && <p className="text-slate-400 text-sm">{subtitle}</p>}
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
                title={compareActive ? "In the compare tray (click to remove)" : "Add to compare"} aria-label={compareActive ? "Remove from the compare tray" : "Add to compare"} aria-pressed={compareActive}>
                <ArrowRightLeft size={16} />
              </button>
            )}
            <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
              <X size={20} />
            </button>
          </div>
        </div>
        {/* inside the shell, so a failing section leaves the close button working */}
        <ErrorBoundary scope="this panel" compact key={title}>{children}</ErrorBoundary>
      </div>
    </motion.div>
  );
}
