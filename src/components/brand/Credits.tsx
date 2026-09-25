import React from 'react';
import { MessageSquare } from 'lucide-react';
import { cn } from '../../utils/cn';

const asset = (name: string) => import.meta.env.BASE_URL + 'assets/' + name;

/** Where people reach the team: comments, suggestions, or a simulant they have made. */
export const FEEDBACK_URL = 'https://thespringinstitute.com/contact-us/';

/**
 * The sponsor and the developer, on a light tile so both logos keep their own colours
 * (the CNES blue disappears on the dark panes). `splash` for the loading screen, `pane` for
 * the foot of the Find pane.
 */
export function Credits({ variant }: { variant: 'splash' | 'pane' }) {
  const splash = variant === 'splash';
  const Item = ({ label, href, children }: { label: string; href: string; children: React.ReactNode }) => {
    const body = (
      <>
        <span className={cn('uppercase tracking-wider text-slate-500', splash ? 'text-[10px]' : 'text-[9px]')}>{label}</span>
        <span className="flex items-center gap-2">{children}</span>
      </>
    );
    const cls = cn('flex flex-col items-center no-underline', splash ? 'gap-1.5' : 'gap-0.5');
    // on the loading screen the tile is not a link: a click there should not leave the page
    return splash ? <div className={cls}>{body}</div>
      : <a href={href} target="_blank" rel="noopener noreferrer" className={cn(cls, 'rounded-md hover:opacity-80')}>{body}</a>;
  };
  return (
    <div className={cn('flex items-center justify-center rounded-xl bg-white shadow-sm', splash ? 'gap-8 px-8 py-5' : 'gap-4 px-3 py-1.5')}>
      <Item label="Sponsored by" href="https://cnes.fr">
        <img src={asset('cnes-logo-320.png')} alt="CNES, Centre national d'études spatiales" className={splash ? 'h-14 w-auto' : 'h-8 w-auto'} />
      </Item>
      <div className={cn('w-px bg-slate-200', splash ? 'h-14' : 'h-8')} aria-hidden />
      <Item label="Developed by" href="https://thespringinstitute.com">
        <img src={asset('spring-logo.png')} alt="" className={splash ? 'h-12 w-auto' : 'h-6 w-auto'} />
        <span className={cn('font-semibold leading-tight text-slate-800', splash ? 'text-sm' : 'text-[11px]')}>The Spring<br />Institute</span>
      </Item>
    </div>
  );
}

/** A clear way to reach the team, at the foot of the Find pane. */
export function FeedbackLink() {
  return (
    <a href={FEEDBACK_URL} target="_blank" rel="noopener noreferrer"
      className="flex items-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-3 py-1.5 no-underline transition-colors hover:bg-emerald-500/10">
      <MessageSquare size={16} className="shrink-0 text-emerald-400" aria-hidden />
      <span className="min-w-0">
        <span className="block text-sm font-medium text-emerald-400">Send us feedback</span>
        <span className="block text-[11px] leading-snug text-slate-400">Comments, suggestions, or a new simulant you have made</span>
      </span>
    </a>
  );
}
