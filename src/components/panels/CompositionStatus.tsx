import { ShieldCheck, FileX2, FileText, HelpCircle, ExternalLink } from 'lucide-react';
import type { Simulant } from '../../types';

export type CompositionStatus =
  | 'verified'
  | 'withheld_unverified'
  | 'not_published'
  | 'not_extracted';

// Shown where a composition table would be, when there is none to show. Worded for readers of
// the database: what is known about this simulant's composition, not how the data was checked.
const NOTICES: Record<CompositionStatus, { title: string; body: string; tone: string; Icon: typeof ShieldCheck }> = {
  // the composition source gives the other table (chemistry without minerals, or the reverse)
  verified: {
    title: 'Not given by the source',
    body: 'The source of this simulant\'s composition does not give this table.',
    tone: 'text-slate-400',
    Icon: FileX2,
  },
  withheld_unverified: {
    title: 'Not available',
    body: 'We could not trace a composition for this simulant to its data sheet or to the paper that describes it, so none is shown.',
    tone: 'text-slate-400',
    Icon: HelpCircle,
  },
  not_published: {
    title: 'Not published',
    body: 'The producer and the paper that describes this simulant do not publish a composition for it.',
    tone: 'text-slate-400',
    Icon: FileX2,
  },
  not_extracted: {
    title: 'Not available yet',
    body: 'We have not yet found a source for this simulant\'s composition.',
    tone: 'text-slate-400',
    Icon: HelpCircle,
  },
};

export function statusOf(simulant: Pick<Simulant, 'composition_status'>): CompositionStatus {
  const s = simulant.composition_status;
  if (s === 'verified' || s === 'withheld_unverified' || s === 'not_published') return s;
  return 'not_extracted';
}

/** Empty-state notice shown in place of a composition chart. */
export function CompositionStatusNotice({
  status,
  kind,
}: {
  status: CompositionStatus;
  kind: 'mineral' | 'chemical' | 'composition';
}) {
  const n = NOTICES[status];
  const what = kind === 'mineral' ? 'Mineral composition' : kind === 'chemical' ? 'Chemical composition' : 'Composition';
  return (
    <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
      <div className="flex items-start gap-3">
        <n.Icon size={18} className={`${n.tone} mt-0.5 shrink-0`} aria-hidden />
        <div>
          <p className={`text-sm font-semibold ${n.tone}`}>
            {what}: {n.title.charAt(0).toLowerCase() + n.title.slice(1)}
          </p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">{n.body}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * The one line that says where a simulant's published numbers came from.
 * Deliberately separate from the reference list, which holds usage studies.
 */
export function DataSourceLine({ simulant }: { simulant: Simulant }) {
  const status = statusOf(simulant);
  if (status !== 'verified') return null;

  const title = simulant.composition_source_title || 'Source on file';
  // Only a web address may become a link. The audit's working copies live on local
  // disk; a local path rendered as an href resolves against this site and 404s.
  const candidate = simulant.composition_source_url || simulant.datasheet_url || '';
  const url = /^https?:\/\//i.test(candidate) ? candidate : '';
  const kindLabel =
    simulant.composition_source_kind === 'manufacturer_datasheet'
      ? 'Manufacturer data sheet'
      : simulant.composition_source_kind === 'primary_paper'
        ? 'Primary characterisation paper'
        : simulant.composition_source_kind === 'agency_report'
          ? 'Agency report'
          : simulant.composition_source_kind === 'secondary_reproduction'
            ? 'As reproduced in a later publication'
            : 'Source';

  return (
    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-4 py-3">
      <div className="flex items-start gap-3">
        <FileText size={16} className="text-emerald-400 mt-0.5 shrink-0" aria-hidden />
        <div className="min-w-0">
          <p className="text-[10px] uppercase font-bold tracking-wider text-emerald-400/70">
            Source of the composition
          </p>
          <p className="text-sm text-slate-200 mt-0.5 break-words">
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-emerald-300 underline decoration-emerald-500/40 underline-offset-2"
              >
                {title}
                <ExternalLink size={12} className="inline ml-1 mb-0.5" aria-hidden />
              </a>
            ) : (
              title
            )}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {kindLabel}
            {simulant.datasheet_date ? ` · ${simulant.datasheet_date}` : ''}
          </p>
          {simulant.datasheet_notes && (
            <details className="mt-1">
              <summary className="text-[11px] text-slate-400 cursor-pointer hover:text-slate-300">
                Methods and caveats stated on the sheet
              </summary>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{simulant.datasheet_notes}</p>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
