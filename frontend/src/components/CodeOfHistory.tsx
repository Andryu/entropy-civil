import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { fetchJson } from '../lib/api';
import type { Epoch, EpochsResponse, HistoryLog, HistoryResponse } from '../types';

export function CodeOfHistory() {
    const [logs, setLogs] = useState<HistoryLog[]>([]);
    const [epochs, setEpochs] = useState<Epoch[]>([]);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const json = await fetchJson<HistoryResponse>('/api/history');
                if (json.logs) {
                    setLogs(json.logs);
                }
            } catch (e) {
                console.error("Failed to fetch history logs", e);
            }
        };

        const fetchEpochs = async () => {
            try {
                const json = await fetchJson<EpochsResponse>('/api/epochs');
                if (json.epochs) {
                    setEpochs(json.epochs);
                }
            } catch (e) {
                console.error("Failed to fetch epochs", e);
            }
        };

        fetchHistory();
        fetchEpochs();

        const historyInterval = setInterval(fetchHistory, 3000);
        const epochInterval = setInterval(fetchEpochs, 10000);

        return () => {
            clearInterval(historyInterval);
            clearInterval(epochInterval);
        };
    }, []);

    return (
        <div className="w-full h-full bg-black flex p-8 pt-24 font-mono">
            {/* Side Visualizer (Evolution Tree) */}
            <div className="w-1/4 border-r border-white/10 flex flex-col gap-4 pr-8">
                <h3 className="text-matrixGreen text-sm border-b border-matrixGreen/30 pb-2 uppercase tracking-widest">
                    進化系統樹 (Evolution Tree)
                </h3>
                <div className="flex-1 relative overflow-y-auto pr-2">
                    <div className="absolute left-4 top-0 bottom-0 w-px bg-white/10" />
                    {epochs.length === 0 && (
                        <div className="text-white/20 text-xs mt-4 ml-8 italic">エポック未検知...</div>
                    )}
                    {epochs.map((epoch) => (
                        <div key={epoch.id} className="flex items-center gap-4 mt-8 relative">
                            <div className="w-3 h-3 rounded-full bg-neonBlue z-10 ml-[10px] shadow-[0_0_8px_#00f3ff]" />
                            <div className="text-xs text-white/50 w-full flex flex-col">
                                <span className="text-neonBlue font-bold">{epoch.name}</span>
                                <div className="flex justify-between mt-1 opacity-60">
                                    <span>ターン {epoch.turn_start}〜</span>
                                    <span>ID:{epoch.id}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Terminal */}
            <div className="flex-1 pl-8 flex flex-col justify-end overflow-hidden pb-8 relative">
                <div className="absolute inset-x-0 top-0 h-24 pointer-events-none bg-gradient-to-b from-black to-transparent z-10" />
                <div className="flex flex-col gap-2 relative z-0">
                    {logs.map((log, idx) => {
                        const structured = log.structured ?? {
                            actor: log.actor,
                            action: log.action,
                            target: log.target,
                            location: log.location,
                            cause: log.cause,
                            effect: log.effect,
                            tags: log.tags,
                            importance: log.importance,
                            entropy_level: log.entropy_level,
                            causal_parent_id: log.causal_parent_id,
                        };
                        const summaryBits = [
                            structured.actor && `actor:${structured.actor}`,
                            structured.action && `action:${structured.action}`,
                            structured.location && `location:${structured.location}`,
                            structured.target && `target:${structured.target}`,
                            structured.causal_parent_id != null && `parent:#${structured.causal_parent_id}`,
                        ].filter(Boolean) as string[];
                        const tagBits = structured.tags?.length
                            ? structured.tags.map((tag) => `#${tag}`)
                            : [];

                        return (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                key={log.id || idx}
                                className={`text-sm ${log.content?.includes('[エントロピー注入]') || log.type === 'REFLECTION' ? 'text-neonPurple font-bold' :
                                    log.type === 'CLOUD_SUMMARY' ? 'text-neonBlue' :
                                        log.content?.includes('-->') ? 'text-matrixGreen/70' :
                                            'text-white/60'
                                    }`}
                            >
                                <div>
                                    <span className="opacity-40 mr-4">T-{log.turn}</span>
                                    <span className="opacity-40 mr-4 text-xs">[{log.type}]</span>
                                    {log.content}
                                </div>
                                {(summaryBits.length > 0 || tagBits.length > 0) && (
                                    <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-white/35">
                                        {summaryBits.map((bit) => (
                                            <span key={bit} className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5">
                                                {bit}
                                            </span>
                                        ))}
                                        {tagBits.map((bit) => (
                                            <span key={bit} className="rounded-full border border-neonBlue/20 bg-neonBlue/10 px-2 py-0.5 text-neonBlue/80">
                                                {bit}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </motion.div>
                        );
                    })}
                    {logs.length === 0 && (
                        <div className="text-white/20 italic">シミュレーションログ待機中... (Waiting for logs...)</div>
                    )}
                </div>
                <div className="mt-4 flex items-center gap-2 text-matrixGreen text-sm animate-pulse">
                    <span>_</span>
                    <span>リアルタイム観測中... (Observing real-time changes...)</span>
                </div>
            </div>
        </div>
    );
}
