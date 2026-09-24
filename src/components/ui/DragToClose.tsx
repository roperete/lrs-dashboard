import React from 'react';
import type { DragControls, PanInfo } from 'motion/react';
import { clsx } from 'clsx';

/** The edge a panel leaves through: the right pane goes right (down on phones), the sidebar left. */
export type CloseDirection = 'left' | 'right' | 'down';

/** Drag past this many pixels, or flick faster than CLOSE_VELOCITY px/s, and the panel closes. */
const CLOSE_DISTANCE = 120;
const CLOSE_VELOCITY = 600;

/**
 * Motion props that let a panel be dragged towards its own edge by its grip only (dragListener
 * off, so text selection and scrolling inside the panel are unaffected). Released short of the
 * threshold, it springs back.
 */
export function dragToClose(direction: CloseDirection, controls: DragControls, onClose: () => void) {
  const axis = direction === 'down' ? 'y' : 'x';
  const sign = direction === 'left' ? -1 : 1;
  return {
    drag: axis,
    dragControls: controls,
    dragListener: false,
    dragConstraints: { left: 0, right: 0, top: 0, bottom: 0 },
    dragElastic: direction === 'left' ? { left: 1, right: 0 } : direction === 'right' ? { left: 0, right: 1 } : { top: 0, bottom: 1 },
    dragSnapToOrigin: true,
    onDragEnd: (_: unknown, info: PanInfo) => {
      const distance = sign * (axis === 'x' ? info.offset.x : info.offset.y);
      const speed = sign * (axis === 'x' ? info.velocity.x : info.velocity.y);
      if (distance > CLOSE_DISTANCE || speed > CLOSE_VELOCITY) onClose();
    },
  } as const;
}

/**
 * The grip on a panel's inner edge (a short bar, lighter on hover). Pressing it starts the drag;
 * with the keyboard, Enter or Space closes the panel.
 */
export function DragGrip({ direction, controls, onClose }: { direction: CloseDirection; controls: DragControls; onClose: () => void }) {
  const vertical = direction !== 'down';
  const hint = direction === 'left' ? 'Drag left to close' : direction === 'right' ? 'Drag right to close' : 'Drag down to close';
  return (
    <div
      role="button" tabIndex={0}
      aria-label={`Close panel (${hint.toLowerCase()})`}
      title={hint}
      onPointerDown={(e) => controls.start(e)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClose(); } }}
      style={{ touchAction: 'none' }}
      className={clsx(
        'group absolute z-10 flex items-center justify-center cursor-grab active:cursor-grabbing focus:outline-none',
        direction === 'right' && 'left-0 top-0 h-full w-4 -translate-x-1/2',
        direction === 'left' && 'right-0 top-0 h-full w-4 translate-x-1/2',
        direction === 'down' && 'top-0 left-0 w-full h-6',
      )}
    >
      <span className={clsx(
        'rounded-full bg-slate-600 group-hover:bg-slate-400 group-focus-visible:bg-emerald-400 transition-colors',
        vertical ? 'h-12 w-1.5' : 'w-12 h-1.5',
      )} />
    </div>
  );
}
