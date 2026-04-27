import { useEffect, useState, useRef } from 'react';
import { fetchJson } from '../lib/api';
import type { AgentState, SandboxState, WorldLocation } from '../types';

export function SandboxWorld() {
    const [state, setState] = useState<SandboxState | null>(null);
    const mapRef = useRef<HTMLDivElement>(null);

    // Poll for state every 2 seconds
    useEffect(() => {
        const fetchState = async () => {
            try {
                const data = await fetchJson<SandboxState & { error?: string }>('/api/sandbox/state');
                if (!data.error) {
                    setState(data);
                }
            } catch (err) {
                console.error("Failed to fetch sandbox state:", err);
            }
        };

        fetchState();
        const interval = setInterval(fetchState, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="w-full h-full relative overflow-hidden bg-gray-900 flex items-center justify-center">
            {/* Background World Map */}
            <div
                ref={mapRef}
                className="relative shadow-2xl rounded-2xl border border-gray-700 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTIwIDB2NDBtbS0yMC0yMGg0MCIgc3Ryb2tlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIiBzdHJva2Utd2lkdGg9IjEiIGZpbGw9Im5vbmUiLz48L3N2Zz4=')] bg-repeat"
                style={{
                    width: '800px',
                    height: '600px',
                    backgroundColor: '#1a202c', // Dark modern map background
                }}
            >
                {/* Render World Locations */}
                {state?.world?.locations.map(location => (
                    <LocationMarker key={location.id} location={location} />
                ))}

                {/* Render Agents */}
                {state && state.agents.map(agent => (
                    <AgentIcon key={agent.id} agent={agent} />
                ))}

                {!state && (
                    <div className="absolute inset-0 flex items-center justify-center text-white/50 animate-pulse">
                        Waiting for simulation to start...
                    </div>
                )}
            </div>

            <div className="absolute top-4 left-4 glass-panel px-4 py-2 flex gap-4 text-sm font-mono text-white/70">
                <div>Turn: <span className="text-neonBlue">{state?.turn ?? 0}</span></div>
                <div>Agents: <span className="text-neonBlue">{state?.agents.length ?? 0}</span></div>
                <div>Weather: <span className="text-neonBlue">{state?.world?.weather ?? 'unknown'}</span></div>
            </div>

            {state?.world && (
                <div className="absolute top-16 left-4 glass-panel px-4 py-3 text-xs font-mono text-white/70 w-64">
                    <div className="text-white/90 font-bold mb-2">World resources</div>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-1">
                        {Object.entries(state.world.resources).map(([name, value]) => (
                            <div key={name} className="flex justify-between gap-2">
                                <span className="capitalize">{name}</span>
                                <span className="text-neonBlue">{value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {state?.world?.beliefs?.length ? (
                <div className="absolute top-16 right-4 glass-panel px-4 py-3 text-xs font-mono text-white/70 w-72 max-h-[260px] overflow-auto">
                    <div className="text-white/90 font-bold mb-2">Active beliefs</div>
                    <div className="space-y-2">
                        {state.world.beliefs.slice(-6).reverse().map((belief, index) => (
                            <div key={`${belief.kind}-${belief.source_agent_id}-${belief.source_turn}-${index}`} className="border border-white/10 rounded bg-black/30 p-2">
                                <div className="flex items-center justify-between gap-2 text-[10px] uppercase tracking-wide text-neonBlue">
                                    <span>{belief.kind.replace('_', ' ')}</span>
                                    <span>turn {belief.source_turn}</span>
                                </div>
                                <div className="mt-1 text-white/85 leading-snug">{belief.text}</div>
                                <div className="mt-1 text-[10px] text-white/45">
                                    from {belief.source_agent_id} · strength {belief.strength.toFixed(2)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : null}
        </div>
    );
}

function LocationMarker({ location }: { location: WorldLocation }) {
    const left = 20 + (location.x / 100) * 760;
    const top = 20 + (location.y / 100) * 560;
    const icon = biomeIcon(location.biome);

    return (
        <div
            className="absolute flex flex-col items-center text-white/70"
            style={{
                left: `${left}px`,
                top: `${top}px`,
                transform: 'translate(-50%, -50%)'
            }}
            title={`${location.name} / ${location.resources.join(', ')} / activity ${location.activity}`}
        >
            <div className="text-2xl opacity-80 drop-shadow-[0_0_10px_rgba(255,255,255,0.25)]">
                {icon}
            </div>
            <div className="mt-1 text-[10px] font-bold tracking-wide bg-black/50 px-2 py-0.5 rounded border border-white/10">
                {location.name}
            </div>
            {location.activity > 0 && (
                <div className="mt-1 text-[9px] text-neonBlue bg-black/60 px-1 rounded">
                    activity {location.activity}
                </div>
            )}
        </div>
    );
}

function biomeIcon(biome: string) {
    switch (biome) {
        case 'water':
            return '🌊';
        case 'forest':
            return '🌲';
        case 'settlement':
            return '🔥';
        case 'stone':
            return '⛰️';
        case 'grassland':
            return '🌾';
        default:
            return '◇';
    }
}

function AgentIcon({ agent }: { agent: AgentState }) {
    // Map 0-100 coordinates to actual pixel sizes (800x600)
    // Give some padding so they don't go exactly to the edge
    const left = 20 + (agent.x / 100) * 760;
    const top = 20 + (agent.y / 100) * 560;

    return (
        <div
            className="absolute flex flex-col items-center transition-all duration-[2000ms] ease-linear"
            style={{
                left: `${left}px`,
                top: `${top}px`,
                transform: 'translate(-50%, -50%)'
            }}
        >
            {/* Speech Bubble */}
            {agent.speech && (
                <div className="mb-2 max-w-[150px] bg-white/10 backdrop-blur-md text-xs p-2 rounded border border-white/20 shadow-lg relative animate-fade-in text-white/90">
                    {agent.speech}
                    <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white/20 rotate-45 border-r border-b border-white/20"></div>
                </div>
            )}

            {/* Emotion / Status Icon */}
            <div className="absolute -top-6 text-xl filter drop-shadow hover:scale-125 transition-transform cursor-help" title={agent.action}>
                {agent.emotion}
            </div>

            {/* Agent Dot (The character) */}
            <div className="w-4 h-4 rounded-full bg-neonBlue shadow-[0_0_10px_rgba(0,243,255,0.8)] relative animate-bounce-slow">
                {/* Shadow under the dot */}
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-4 h-1 bg-black/50 rounded-full blur-[2px]"></div>
            </div>

            {/* Name */}
            <div className="mt-1 text-[10px] uppercase font-bold tracking-wider text-white/50 bg-black/50 px-1 rounded">
                {agent.name}
            </div>
        </div>
    );
}
