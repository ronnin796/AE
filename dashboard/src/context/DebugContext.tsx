import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from "react";
import { DebugEvent } from "../types";
import { useDebugEvents } from "../hooks/useTelemetry";

export interface SystemEvent {
  id: number;
  timestamp: string;
  type: "connect" | "disconnect" | "heartbeat" | "telemetry" | "command" | "error";
  node_id: string;
  message: string;
}

interface DebugContextType {
  events: SystemEvent[];
  addEvent: (event: Omit<SystemEvent, "id" | "timestamp">) => void;
  clearEvents: () => void;
}

const DebugContext = createContext<DebugContextType | undefined>(undefined);

export function DebugProvider({ children }: { children: ReactNode }) {
  const [manualEvents, setManualEvents] = useState<SystemEvent[]>([]);
  const { data: apiEventsData } = useDebugEvents(200);
  
  // Convert API events to SystemEvent format
  const apiEvents: SystemEvent[] = React.useMemo(() => {
    if (!apiEventsData?.events) return [];
    return apiEventsData.events.map((e, idx) => ({
      id: e.id ? Number(e.id.split('-').pop()) + 1000000 : idx + 1000000,
      timestamp: e.timestamp,
      type: e.type,
      node_id: e.node_id,
      message: e.message
    }));
  }, [apiEventsData]);

  // Combine manual and API events, deduplicate by timestamp+node+type
  const allEvents = React.useMemo(() => {
    const seen = new Set<string>();
    const combined = [...manualEvents, ...apiEvents];
    
    // Sort by timestamp descending
    combined.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    // Deduplicate
    return combined.filter(e => {
      const key = `${e.timestamp}-${e.node_id}-${e.type}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 200); // Keep last 200
  }, [manualEvents, apiEvents]);

  const addEvent = useCallback((event: Omit<SystemEvent, "id" | "timestamp">) => {
    const newEvent: SystemEvent = {
      ...event,
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
    };
    setManualEvents(prev => [...prev.slice(-199), newEvent]);
  }, []);

  const clearEvents = useCallback(() => setManualEvents([]), []);

  return (
    <DebugContext.Provider value={{ events: allEvents, addEvent, clearEvents }}>
      {children}
    </DebugContext.Provider>
  );
}

export function useDebug() {
  const context = useContext(DebugContext);
  if (!context) {
    throw new Error("useDebug must be used within a DebugProvider");
  }
  return context;
}