import React from 'react';
import { X, Pin, Search, Download, ArrowRightLeft } from 'lucide-react';
import { motion } from 'motion/react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) { return twMerge(clsx(inputs)); }

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
  children: React.ReactNode;
}

export function PanelShell({
  title, subtitle, pinned, onClose, onTogglePin, onSearchSources, onDownload,
  onCompare, compareActive, accentColor = 'text-emerald-400', children,
}: PanelShellProps) {
  return (
    <motion.div
      initial={{ x: '100%', y: 0 }} animate={{ x: 0, y: 0 }} exit={{ x: '100%', y: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 bottom-0 h-[70vh] w-full sm:top-0 sm:bottom-auto sm:h-full sm:w-[450px] bg-slate-900/95 backdrop-blur-xl border-l border-t sm:border-t-0 border-slate-800 z-[1000] overflow-y-auto shadow-2xl rounded-t-2xl sm:rounded-none"
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1 min-w-0">
            <h2 className={cn("text-2xl font-bold tracking-tight truncate", accentColor)}>{title}</h2>
            {subtitle && <p className="text-slate-400 font-mono text-sm uppercase tracking-widest">{subtitle}</p>}
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
