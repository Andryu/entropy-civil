import { useState } from 'react';
import { Database, Orbit, Image as ImageIcon } from 'lucide-react';
import { ConceptUniverse } from './components/ConceptUniverse';
import { CodeOfHistory } from './components/CodeOfHistory';
import { CuratedArtGallery } from './components/CuratedArtGallery';

function App() {
  const [activeTab, setActiveTab] = useState<'universe' | 'code' | 'art'>('universe');

  return (
    <div className="h-screen w-screen bg-dark text-white overflow-hidden flex flex-col relative font-display">
      {/* Dynamic Background elements or overlays can go here */}

      {/* Top Navigation */}
      <nav className="absolute top-0 w-full z-50 glass-panel border-b-0 border-white/5 py-4 px-8 flex justify-between items-center">
        <h1 className="text-xl tracking-widest font-bold flex items-center gap-3">
          <span className="text-neonBlue">✦</span> ENTROPY CIVIL <span className="opacity-50 text-sm">v0.1.0</span>
        </h1>

        <div className="flex gap-4">
          <TabButton
            active={activeTab === 'universe'}
            onClick={() => setActiveTab('universe')}
            icon={<Orbit size={18} />}
            label="Concept Universe"
          />
          <TabButton
            active={activeTab === 'code'}
            onClick={() => setActiveTab('code')}
            icon={<Database size={18} />}
            label="Code of History"
          />
          <TabButton
            active={activeTab === 'art'}
            onClick={() => setActiveTab('art')}
            icon={<ImageIcon size={18} />}
            label="Curatorial Gallery"
          />
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 relative w-full h-full">
        {activeTab === 'universe' && <ConceptUniverse />}
        {activeTab === 'code' && <CodeOfHistory />}
        {activeTab === 'art' && <CuratedArtGallery />}
      </main>

    </div>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-300 font-mono text-sm ${active
        ? 'bg-white/10 text-neonBlue border border-neonBlue/30 shadow-[0_0_15px_rgba(0,243,255,0.2)]'
        : 'text-white/60 hover:text-white hover:bg-white/5 border border-transparent'
        }`}
    >
      {icon}
      {label}
    </button>
  );
}

export default App;
