import { motion } from 'framer-motion';
import { Upload, Star } from 'lucide-react';

const MOCK_PROMPT = `A highly detailed, cinematic shot of a primitive tribal gathering around a massive glowing monolithic stone (The First Memory). Ethereal lighting, volumetric mist, ancient clothing, hyper-realistic, 8k resolution, inspired by Denis Villeneuve, mystical atmosphere --ar 16:9 --v 6.0`;

export function CuratedArtGallery() {
    return (
        <div className="w-full h-full p-8 pt-24 flex gap-8">
            {/* Left sidebar: Prompt Generator Output */}
            <div className="w-1/3 flex flex-col gap-6">
                <div className="glass-panel p-6 rounded-xl border-neonPurple/40 h-full flex flex-col">
                    <h2 className="text-neonPurple font-bold flex items-center gap-2 mb-4">
                        <Star size={18} /> 生成された究極のプロンプト (MASTER PROMPT)
                    </h2>
                    <p className="text-sm text-white/60 mb-4 flex-1">
                        システムがターン50を解析しました。「最初の記憶」の神話が臨界点に達しています。以下のプロンプトをMidjourneyやNanoBananaで使用してださい：
                    </p>
                    <div className="bg-black/50 p-4 rounded-lg font-mono text-xs text-white/80 border border-white/10 leading-relaxed mb-4">
                        {MOCK_PROMPT}
                    </div>
                    <button className="w-full py-3 bg-white/10 hover:bg-white/20 transition-all rounded-lg text-sm font-bold flex items-center justify-center gap-2">
                        プロンプトをコピー (Copy Prompt)
                    </button>
                </div>
            </div>

            {/* Right side: Gallery & Upload */}
            <div className="w-2/3 flex flex-col gap-4">
                <div className="h-32 rounded-xl border border-dashed border-white/20 bg-white/5 flex flex-col items-center justify-center text-white/40 hover:text-white/80 hover:border-white/50 transition-all cursor-pointer">
                    <Upload size={24} className="mb-2" />
                    <span className="text-sm font-bold tracking-widest">生成したアートワークをドラッグ＆ドロップ (DRAG & DROP ARTWORK)</span>
                </div>

                {/* Gallery Grid */}
                <div className="flex-1 grid grid-cols-2 gap-4 auto-rows-fr">
                    {/* Mock Uploaded image placeholder */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="rounded-xl overflow-hidden relative group border border-white/10"
                    >
                        <div className="absolute inset-0 bg-gradient-to-tr from-neonPurple/20 to-neonBlue/20" />
                        <div className="absolute inset-0 flex items-center justify-center text-white/20 font-bold tracking-widest">
                            [ アートワークのプレースホルダー ]
                        </div>
                        {/* Overlay metadata */}
                        <div className="absolute bottom-0 left-0 w-full p-4 bg-gradient-to-t from-black to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                            <h3 className="font-bold text-sm">エポック 50: 最初の記憶 (Epoch 50: The First Memory)</h3>
                            <p className="text-xs text-white/60">システムによるキュレーション (Curated by System)</p>
                        </div>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
