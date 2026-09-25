import React from 'react';
import { APP_VERSION } from '../../version';

interface State { error: Error | null }
interface Props {
  scope: string; children: React.ReactNode; hint?: React.ReactNode;
  /** 'page' fills the screen; 'area' centres the message in a view; 'inline' sits in a panel. */
  compact?: boolean; area?: boolean;
  /** Told when this part fails, so the loading screen does not wait for a view that cannot draw. */
  onError?: () => void;
}

/**
 * Catches a render error anywhere below it and says what failed, instead of React unmounting
 * the whole page to a blank screen (v2.9.17: one empty field in the search did exactly that).
 * `scope` names the part of the page, so an error in one view can leave the rest usable.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  // the project has no @types/react, so the inherited members are declared here
  declare props: Props;
  declare setState: (s: State) => void;
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(`[${this.props.scope}]`, error, info.componentStack);
    this.props.onError?.();
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    const box = (
      <div role="alert" className="max-w-md rounded-xl border border-red-500/30 bg-slate-900 p-5 text-sm text-slate-300 shadow-2xl">
        <p className="font-semibold text-red-300 mb-1">Something on this page failed ({this.props.scope}).</p>
        <p className="text-slate-400 mb-3">The error was: <span className="font-mono text-slate-300">{error.message}</span></p>
        {this.props.hint && <p className="text-slate-300 mb-3">{this.props.hint}</p>}
        <div className="flex gap-2">
          <button onClick={() => this.setState({ error: null })}
            className="rounded-lg border border-slate-600 px-3 py-1.5 hover:bg-slate-800">Try again</button>
          <button onClick={() => window.location.reload()}
            className="rounded-lg bg-emerald-500 px-3 py-1.5 font-medium text-slate-950 hover:bg-emerald-400">Reload the page</button>
        </div>
        <p className="mt-3 text-xs text-slate-400">Please mention {APP_VERSION} and what you clicked in the Feedback form.</p>
      </div>
    );
    if (this.props.area) return <div className="flex h-full w-full items-center justify-center p-4">{box}</div>;
    return this.props.compact ? <div className="p-4">{box}</div>
      : <div className="flex h-dvh w-screen items-center justify-center bg-slate-950 p-4">{box}</div>;
  }
}
