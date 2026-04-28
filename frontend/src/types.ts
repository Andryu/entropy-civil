export interface AgentState {
  id: string;
  name: string;
  x: number;
  y: number;
  emotion: string;
  action: string;
  speech: string;
  location_id?: string | null;
}

export interface WorldLocation {
  id: string;
  name: string;
  x: number;
  y: number;
  biome: string;
  resources: string[];
  activity: number;
  last_event: string;
}

export interface WorldBelief {
  kind: string;
  text: string;
  source_agent_id: string;
  source_turn: number;
  strength: number;
  trigger: string;
}

export interface WorldState {
  weather: string;
  resources: Record<string, number>;
  locations: WorldLocation[];
  beliefs: WorldBelief[];
  events: Array<{
    agent_id: string;
    location_id: string;
    resource_id: string;
    effect: string;
    amount: number;
    description: string;
  }>;
}

export interface SandboxState {
  turn: number;
  agents: AgentState[];
  world?: WorldState;
}

export interface UniverseParticleData {
  id: string;
  text: string;
  position: [number, number, number];
  importance: number;
  isLegend: boolean;
  agent_id: string;
}

export interface UniverseResponse {
  data?: UniverseParticleData[];
  error?: string;
}

export interface StructuredHistoryData {
  actor?: string | null;
  action?: string | null;
  target?: string | null;
  location?: string | null;
  cause?: string | null;
  effect?: string | null;
  tags?: string[];
  importance?: number | null;
  entropy_level?: number | null;
  causal_parent_id?: number | null;
}

export interface HistoryLog {
  id: number;
  turn: number;
  type: string;
  content: string;
  structured?: StructuredHistoryData;
  actor?: string | null;
  action?: string | null;
  target?: string | null;
  location?: string | null;
  cause?: string | null;
  effect?: string | null;
  tags?: string[];
  importance?: number | null;
  entropy_level?: number | null;
  causal_parent_id?: number | null;
}

export interface HistoryResponse {
  logs?: HistoryLog[];
}

export interface Epoch {
  id: number;
  name: string;
  turn_start: number;
  turn_end?: number | null;
  master_prompt?: string | null;
  image_url?: string | null;
}

export interface EpochsResponse {
  epochs?: Epoch[];
}
