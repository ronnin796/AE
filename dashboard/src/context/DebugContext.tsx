import React, { createContext, useContext, useState, ReactNode, useCallback } from "react";

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
  const [events, setEvents] = useState<SystemEvent[]>([]);

  const addEvent = useCallback((event: Omit<SystemEvent, "id" | "timestamp">) => {
    const newEvent: SystemEvent = {
      ...event,
      id: Date.now() + Math.random(), // Ensure unique IDs
      timestamp: new Date().toISOString(),
    };
    setEvents(prev => [...prev.slice(-199), newEvent]); // Keep last 200 events
  }, []);

  const clearEvents = useCallback(() => setEvents([]), []);

  return (
    <DebugContext.Provider value={{ events, addEvent, clearEvents }}>
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