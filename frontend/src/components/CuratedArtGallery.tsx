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
                <input
                    type="file"
                    id="artwork-upload"
                    className="hidden"
                    accept="image/*"
                    onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file || !latestEpoch) return;

                        const formData = new FormData();
                        formData.append('file', file);

                        try {
                            const res = await fetch(`${API_BASE}/api/epochs/${latestEpoch.id}/upload`, {
                                method: 'POST',
                                body: formData,
                            });

                            if (res.ok) {
                                // Refresh epochs to show new image
                                const epochRes = await fetch(`${API_BASE}/api/epochs`);
                                const json = await epochRes.json();
                                if (json.epochs) {
                                    setEpochs(json.epochs.reverse());
                                }
                            } else {
                                console.error("Upload failed", await res.text());
                            }
                        } catch (err) {
                            console.error("Upload error", err);
                        }

                        // Reset input
                        e.target.value = '';
                    }}
                />
                <button
                    onClick={() => document.getElementById('artwork-upload')?.click()}
                    disabled={!latestEpoch}
                    className="h-32 w-full rounded-xl border border-dashed border-white/20 bg-white/5 flex flex-col items-center justify-center text-white/40 hover:text-white/80 hover:border-white/50 hover:bg-white/10 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Upload size={24} className="mb-2" />
                    <span className="text-sm font-bold tracking-widest">
                        {latestEpoch ? `生成したアートワークをアップロード [ ${latestEpoch.name} ]` : 'エポックを待機中'}
                    </span>
                </button>

                {/* Gallery Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {epochs.map((epoch) => (
                        <motion.div
                            key={epoch.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="rounded-xl overflow-hidden relative group border border-white/10 aspect-video bg-black"
                        >
                            {epoch.image_url ? (
                                <img
                                    src={`${API_BASE}${epoch.image_url}?t=${Date.now()}`} // Cache buster
                                    alt={epoch.name}
                                    className="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110"
                                />
                            ) : (
                                <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-tr from-neonPurple/10 to-neonBlue/10 p-4 text-center">
                                    <div className="text-white/20 font-bold tracking-widest mb-2">
                                        [ {epoch.name} ]
                                    </div>
                                    <div className="text-xs text-white/40">
                                        アートワーク未登録
                                    </div>
                                </div>
                            )}

                            {/* Overlay metadata */}
                            <div className="absolute bottom-0 left-0 w-full p-4 bg-gradient-to-t from-black to-transparent opacity-80 group-hover:opacity-100 transition-opacity">
                                <h3 className="font-bold text-sm">{epoch.name}</h3>
                                <p className="text-xs text-white/60">Turn {epoch.turn_start}{epoch.turn_end ? ` - ${epoch.turn_end}` : ''}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
