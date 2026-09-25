import { useState, useCallback } from 'react';
import type { PanelState } from '../types';

const defaultPanel: PanelState = { open: false, simulantId: null };

/** A pane section a click can open at: the table's Chem/Miner and References cells use them. */
export type PaneSection = 'composition' | 'references';

/** At most this many simulants in the compare tray. */
export const MAX_COMPARE = 4;

export function usePanelState() {
  const [panel1, setPanel1] = useState<PanelState>(defaultPanel);
  const [focusSection, setFocusSection] = useState<PaneSection | null>(null);
  // The compare tray: the pane's "Add to compare", the table's and the list's checkboxes all
  // add here, and the tray opens the comparison (review #6: one mechanism instead of three).
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [selectedLunarSiteId, setSelectedLunarSiteId] = useState<string | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  // The lunar sample the user picked, and for which simulant: a pick applies to that simulant
  // only, so the next one opens with its own suggestion instead of the previous choice.
  const [lunarRefPick, setLunarRefPick] = useState<{ simulantId: string; mission: string | null } | null>(null);
  const [showCrossComparison, setShowCrossComparison] = useState(false);

  const selectSimulant = useCallback((simulantId: string, section: PaneSection | null = null) => {
    setPanel1({ open: true, simulantId });
    setFocusSection(section);
  }, []);

  const closePanel = useCallback(() => {
    setPanel1(defaultPanel);
    setFocusSection(null);
  }, []);

  const toggleCompare = useCallback((simulantId: string) => {
    setCompareIds(prev => prev.includes(simulantId) ? prev.filter(id => id !== simulantId)
      : prev.length >= MAX_COMPARE ? prev : [...prev, simulantId]);
  }, []);

  const clearCompare = useCallback(() => { setCompareIds([]); setShowComparison(false); }, []);

  return {
    panel1, focusSection, compareIds, showComparison,
    selectedLunarSiteId, lunarRefPick, showCrossComparison,
    selectSimulant, closePanel, toggleCompare, clearCompare, setCompareIds,
    setSelectedLunarSiteId,
    setShowComparison,
    setLunarRefPick, setShowCrossComparison,
  };
}
