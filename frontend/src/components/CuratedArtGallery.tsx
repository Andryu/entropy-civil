import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Upload, Star, Copy, Check } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export function CuratedArtGallery() {
    const [epochs, setEpochs] = useState<any[]>([]);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const fetchEpochs = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/epochs`);
                const json = await res.json();
                if (json.epochs) {
                    setEpochs(json.epochs.reverse()); // Latest first
                }
            } catch (e) {
                console.error("Failed to fetch epochs", e);
            }
        };
        fetchEpochs();
    }, []);

    const latestEpoch = epochs[0];

    const copyToClipboard = () => {
        if (latestEpoch?.master_prompt) {
            navigator.clipboard.writeText(latestEpoch.master_prompt);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="w-full h-full p-8 pt-24 flex flex-col md:flex-row gap-8 overflow-y-auto">
            {/* Left sidebar: Prompt Generator Output */}
            <div className="w-full md:w-1/3 flex flex-col gap-6">
                <div className="glass-panel p-6 rounded-xl border-neonPurple/40 flex flex-col h-fit">
                    <h2 className="text-neonPurple font-bold flex items-center gap-2 mb-4">
                        <Star size={18} /> 生成された究極のプロンプト (MASTER PROMPT)
                    </h2>
                    {latestEpoch ? (
                        <>
                            <p className="text-sm text-white/60 mb-4">
                                システムがターン {latestEpoch.turn_start} を解析しました。「{latestEpoch.name}」の神話が臨界点に達しています。以下のプロンプトを環境（Midjourney等）で使用してください：
                            </p>
                            <div className="bg-black/50 p-4 rounded-lg font-mono text-xs text-white/80 border border-white/10 leading-relaxed mb-4 break-words">
                                {latestEpoch.master_prompt || "未生成、またはLLMにより生成に失敗しました（None）。シミュレーションの継続をお待ちください。"}
                            </div>
                            <button
                                onClick={copyToClipboard}
                                className="w-full py-3 bg-white/10 hover:bg-white/20 transition-all rounded-lg text-sm font-bold flex items-center justify-center gap-2"
                            >
                                {copied ? <><Check size={16} /> コピー済み</> : <><Copy size={16} /> プロンプトをコピー</>}
                            </button>
                        </>
                    ) : (
                        <p className="text-sm text-white/40 italic">エポックがまだ検出されていません。シミュレーションを進めてください。</p>
                    )}
                </div>
            </div>

            {/* Right side: Gallery & Upload */}
            <div className="w-full md:w-2/3 flex flex-col gap-4">
                <div className="h-32 rounded-xl border border-dashed border-white/20 bg-white/5 flex flex-col items-center justify-center text-white/40 hover:text-white/80 hover:border-white/50 transition-all cursor-pointer">
                    <Upload size={24} className="mb-2" />
                    <span className="text-sm font-bold tracking-widest">生成したアートワークをアップロード (UPLOAD ARTWORK)</span>
                </div>

                {/* Gallery Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {epochs.map((epoch) => (
                        <motion.div
                            key={epoch.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="rounded-xl overflow-hidden relative group border border-white/10 aspect-video bg-black"
                        >
                            <img
                                src={`${API_BASE}${epoch.image_url}`}
                                alt={epoch.name}
                                className="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110"
                                onError={(e) => {
                                    (e.target as any).style.display = 'none';
                                    (e.target as any).nextSibling.style.display = 'flex';
                                }}
                            />
                            <div className="hidden absolute inset-0 flex items-center justify-center text-white/10 font-bold tracking-widest text-center px-4 bg-gradient-to-tr from-neonPurple/10 to-neonBlue/10">
                                [ {epoch.name}のアートを待機中 ]
                            </div>

                            {/* Overlay metadata */}
                            <div className="absolute bottom-0 left-0 w-full p-4 bg-gradient-to-t from-black to-transparent opacity-80 group-hover:opacity-100 transition-opacity">
                                <h3 className="font-bold text-sm">{epoch.name}</h3>
                                <p className="text-xs text-white/60">Turn {epoch.turn_start} - {epoch.turn_end || '?'}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
