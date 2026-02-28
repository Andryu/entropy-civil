import { useRef, useMemo, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Html } from '@react-three/drei';
import * as THREE from 'three';

// Data is now fetched from the backend API
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

function Particle({ position, size, isLegend, text, onClick }: any) {
    const mesh = useRef<THREE.Mesh>(null);
    const [hovered, setHover] = useState(false);

    useFrame((state) => {
        if (!mesh.current) return;
        // Pulse effect for legends
        if (isLegend) {
            const scale = 1 + Math.sin(state.clock.elapsedTime * 2 + position[0]) * 0.3;
            mesh.current.scale.set(scale, scale, scale);
            mesh.current.rotation.y += 0.01;
            mesh.current.rotation.x += 0.01;
        }
        if (hovered) {
            mesh.current.scale.set(1.5, 1.5, 1.5);
        } else if (!isLegend) {
            mesh.current.scale.set(1, 1, 1);
        }
    });

    return (
        <group position={position}>
            <mesh
                ref={mesh}
                onClick={(e) => { e.stopPropagation(); onClick(); }}
                onPointerOver={(e) => { e.stopPropagation(); setHover(true); }}
                onPointerOut={() => setHover(false)}
            >
                {isLegend ? <icosahedronGeometry args={[size, 1]} /> : <sphereGeometry args={[size, 16, 16]} />}
                <meshBasicMaterial
                    color={hovered ? '#bc13fe' : (isLegend ? '#00f3ff' : '#ffffff')}
                    wireframe={isLegend}
                    transparent
                    opacity={isLegend ? 0.9 : 0.4}
                    blending={THREE.AdditiveBlending}
                    depthWrite={false}
                />
            </mesh>
            {hovered && (
                <Html position={[0, size + 0.5, 0]} center style={{ pointerEvents: 'none' }}>
                    <div className="bg-black/80 text-neonBlue border border-neonBlue/50 px-3 py-1 rounded font-mono text-xs whitespace-nowrap shadow-[0_0_10px_rgba(0,243,255,0.3)]">
                        {text}
                    </div>
                </Html>
            )}
        </group>
    );
}

function Universe() {
    const [selected, setSelected] = useState<any>(null);
    const [memories, setMemories] = useState<any[]>([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/universe`);
                const json = await res.json();
                if (json.data) {
                    setMemories(json.data);
                }
            } catch (e) {
                console.error("Failed to fetch universe data", e);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const particles = useMemo(() => memories.map((data, i) => (
        <Particle
            key={data.id || i}
            {...data}
            size={data.isLegend ? 0.8 : 0.15}
            onClick={() => setSelected(data)}
        />
    )), [memories]);

    // constellation lines between legends
    const legendLines = useMemo(() => {
        const legends = memories.filter(m => m.isLegend);
        if (legends.length < 2) return null;

        const lineGeometry = new THREE.BufferGeometry();
        const positions = [];

        // Connect each legend to its nearest neighbors to form a constellation
        const K = Math.min(3, legends.length - 1);
        const drawnPairs = new Set<string>();

        for (let i = 0; i < legends.length; i++) {
            const p1 = new THREE.Vector3(...legends[i].position);

            const distances = [];
            for (let j = 0; j < legends.length; j++) {
                if (i !== j) {
                    const p2 = new THREE.Vector3(...legends[j].position);
                    distances.push({ index: j, distance: p1.distanceToSquared(p2) });
                }
            }

            distances.sort((a, b) => a.distance - b.distance);
            const nearest = distances.slice(0, K);

            for (const { index: j } of nearest) {
                const pairKey = i < j ? `${i}-${j}` : `${j}-${i}`;
                if (!drawnPairs.has(pairKey)) {
                    drawnPairs.add(pairKey);
                    positions.push(...legends[i].position);
                    positions.push(...legends[j].position);
                }
            }
        }

        lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        return (
            <lineSegments geometry={lineGeometry}>
                <lineBasicMaterial color="#00f3ff" transparent opacity={0.3} blending={THREE.AdditiveBlending} />
            </lineSegments>
        );
    }, [memories]);

    return (
        <>
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={1} />
            {particles}
            {legendLines}
            <OrbitControls
                enableDamping
                dampingFactor={0.05}
                maxDistance={80}
            />

            {/* HUD overlay for selected item */}
            {selected && (
                <Html position={[0, -20, 0]} center>
                    <div className="bg-dark/90 border border-matrixGreen p-4 rounded-lg shadow-[0_0_20px_rgba(0,255,65,0.2)] font-mono flex flex-col items-center">
                        <span className="text-matrixGreen/70 text-xs mb-1">選択されたノード (SELECTED NODE)</span>
                        <span className="text-white font-bold">{selected.text}</span>
                        {selected.isLegend && <span className="text-neonBlue text-xs mt-2 animate-pulse">✦ 神話 (MYTH) ✦</span>}
                    </div>
                </Html>
            )}
        </>
    );
}

export function ConceptUniverse() {
    return (
        <div className="w-full h-full relative">
            <Canvas camera={{ position: [0, 0, 40], fov: 60 }}>
                <color attach="background" args={['#050505']} />
                <Stars radius={100} depth={50} count={5000} factor={3} saturation={0.5} fade speed={0.5} />
                <Universe />
            </Canvas>

            <div className="absolute bottom-8 left-8 p-6 glass-panel max-w-sm rounded-xl backdrop-blur-xl border border-neonBlue/20 select-none">
                <h2 className="text-neonBlue font-bold text-lg mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-neonBlue animate-pulse shadow-[0_0_8px_#00f3ff]" />
                    概念宇宙 (CONCEPT UNIVERSE)
                </h2>
                <p className="text-sm text-white/70 font-mono leading-relaxed mb-4">
                    エージェントの記憶と進化する文化的な「概念」のベクトル空間表現。伝説や神話は脈打つ異常な光のクラスターとして顕現します。
                </p>
                <div className="flex flex-col gap-2 text-xs font-mono text-white/50 border-t border-white/10 pt-4">
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full border border-white" /> 通常の概念 (Normal Concept)</div>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-neonBlue animate-pulse" /> 神話・伝説 (Legend / Myth)</div>
                    <div className="mt-2 text-matrixGreen/80">» ドラッグで回転 | スクロールでズーム</div>
                </div>
            </div>
        </div>
    );
}
