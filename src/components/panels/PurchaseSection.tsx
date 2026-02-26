import React from 'react';
import { ExternalLink, ShoppingCart } from 'lucide-react';
import type { PurchaseInfo } from '../../types';

interface PurchaseSectionProps {
  availability: string;
  purchaseInfo?: PurchaseInfo;
}

const STATUS_STYLES: Record<string, string> = {
  'Available': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  'Limited Stock': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  'Production stopped': 'bg-red-500/20 text-red-400 border-red-500/30',
  'Unknown': 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

export function PurchaseSection({ availability, purchaseInfo }: PurchaseSectionProps) {
  const statusStyle = STATUS_STYLES[availability] || STATUS_STYLES['Unknown'];

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Purchase Information</h3>
      <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50 space-y-3">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${statusStyle}`}>
            {availability}
          </span>
        </div>

        {purchaseInfo && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold">Vendor</p>
                <p className="text-sm text-slate-200">{purchaseInfo.vendor}</p>
              </div>
              <a href={purchaseInfo.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg text-xs font-bold transition-colors">
                <ShoppingCart size={12} />
                Visit
                <ExternalLink size={10} />
              </a>
            </div>
            {purchaseInfo.price_note && (
              <p className="text-xs text-slate-400 italic">{purchaseInfo.price_note}</p>
            )}
          </div>
        )}

        {!purchaseInfo && availability === 'Available' && (
          <p className="text-xs text-slate-500 italic">Purchase link not yet cataloged.</p>
        )}
      </div>
    </div>
  );
}
