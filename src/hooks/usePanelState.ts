import { useState, useCallback } from 'react';
import type { PanelState } from '../types';

const defaultPanel: PanelState = { open: false, pinned: false, simulantId: null };

export function usePanelState() {
  const [panel1, setPanel1] = useState<PanelState>(defaultPanel);
  const [panel2, setPanel2] = useState<PanelState>(defaultPanel);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedLunarSiteId, setSelectedLunarSiteId] = useState<string | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedLunarRefMission, setSelectedLunarRefMission] = useState<string | null>(null);
  const [showCrossComparison, setShowCrossComparison] = useState(false);

  const openPanel = useCallback((panelNum: 1 | 2, simulantId: string) => {
    const setter = panelNum === 1 ? setPanel1 : setPanel2;
    setter(prev => ({ ...prev, open: true, simulantId }));
  }, []);

  const closePanel = useCallback((panelNum: 1 | 2) => {
    const setter = panelNum === 1 ? setPanel1 : setPanel2;
    setter(defaultPanel);
    if (panelNum === 1) {
      setCompareMode(false);
      setPanel2(defaultPanel);
    }
  }, []);

  const minimizeUnpinned = useCallback(() => {
    setPanel1(prev => prev.pinned ? prev : { ...prev, open: false });
    setPanel2(prev => prev.pinned ? prev : { ...prev, open: false });
  }, []);

  const togglePin = useCallback((panelNum: 1 | 2) => {
    const setter = panelNum === 1 ? setPanel1 : setPanel2;
    setter(prev => ({ ...prev, pinned: !prev.pinned }));
  }, []);

  const toggleCompare = useCallback(() => {
    setCompareMode(prev => {
      if (prev) setPanel2(defaultPanel);
      return !prev;
    });
  }, []);

  const selectSimulant = useCallback((simulantId: string) => {
    if (compareMode && panel1.open && !panel2.simulantId) {
      openPanel(2, simulantId);
    } else {
      openPanel(1, simulantId);
    }
  }, [compareMode, panel1.open, panel2.simulantId, openPanel]);

  return {
    panel1, panel2, compareMode, showComparison,
    selectedLunarSiteId, selectedLunarRefMission, showCrossComparison,
    openPanel, closePanel, minimizeUnpinned, togglePin, toggleCompare,
    selectSimulant,
    setSelectedLunarSiteId,
    setShowComparison,
    setSelectedLunarRefMission, setShowCrossComparison,
  };
}
