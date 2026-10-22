import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { UploadCloud, Clapperboard, WandSparkles, FolderOpen, Settings2, Play, Pause, RotateCcw, Download, ArrowRight, Film, Monitor, CheckCircle2 } from "lucide-react";
import "./style.css";

type Tab = "dashboard" | "workspace" | "projects";
type Clip = { file: File; url: string; id: string };
function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [clip, setClip] = useState<Clip | null>(null);
  const [resolution, setResolution] = useState("2×");
  const [quality, setQuality] = useState("High Quality");
  const [compare, setCompare] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [notice, setNotice] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const supported = [".mp4", ".mov", ".webm", ".mkv", ".avi"];
  useEffect(() => () => { if (clip) URL.revokeObjectURL(clip.url); }, [clip]);
  const selectFile = (file?: File) => {
    if (!file) return;
    if (!supported.some(ext => file.name.toLowerCase().endsWith(ext))) {
      setNotice("Choose an MP4, MOV, WEBM, MKV, or AVI video."); return;
    }
    setClip({ file, url: URL.createObjectURL(file), id: String(Date.now()) });
    setNotice(""); setProgress(0); setPlaying(false); setCompare(false); setTab("workspace");
  };
  const playToggle = () => {
    if (!video.current) return;
    if (video.current.paused) void video.current.play().catch(() => setNotice("This browser cannot play this video format."));
    else video.current.pause();
  };
  const start = () => setNotice("AI processing is not connected yet. The web workspace is ready; cloud GPU processing and the desktop engine bridge are the next integration steps.");
  const importButton = <button className="primary" onClick={() => input.current?.click()}><UploadCloud size={18}/> Import video <ArrowRight size={17}/></button>;
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-icon">V</span><span>VIDEL<small>AI VIDEO STUDIO</small></span></div>
      <div className="side-label">STUDIO</div>
      <nav>
        <button className={tab==="dashboard"?"active":""} onClick={()=>setTab("dashboard")}><Monitor size={19}/> Dashboard</button>
        <button className={tab==="workspace"?"active":""} onClick={()=>setTab("workspace")}><Clapperboard size={19}/> Workspace</button>
        <button className={tab==="projects"?"active":""} onClick={()=>setTab("projects")}><FolderOpen size={19}/> Projects</button>
      </nav>
      <div className="sidebar-bottom"><span className="status-dot"/> Interface ready <small>AI engine not connected</small></div>
    </aside>
    <main>
      <header className="top"><div><span className="eyebrow">VIDEL / {tab.toUpperCase()}</span><h1>{tab==="workspace"?"Creative Workspace":tab==="projects"?"Your Projects":"Create beyond clarity."}</h1></div><div className="top-right"><span className="web-badge"><span className="status-dot"/> WEB STUDIO</span>{importButton}</div></header>
      {tab==="dashboard" && <section className="hero"><div className="eyebrow lime">AI-POWERED VIDEO ENHANCEMENT</div><h2>Every frame.<br/><em>Extraordinary clarity.</em></h2><p>Bring your footage into a powerful canvas-style workspace. Preview, configure, and prepare your next enhancement.</p>{importButton}<div className="hero-note"><CheckCircle2 size={16}/> Works in your browser • Local preview</div></section>}
      {tab==="projects" && <section className="panel"><h2>Current session</h2>{clip ? <button className="project-card" onClick={()=>setTab("workspace")}><Film size={22}/><span>{clip.file.name}<small>{(clip.file.size/1024/1024).toFixed(1)} MB • Open in workspace</small></span><ArrowRight size={18}/></button> : <p>No video loaded yet. Import a video to begin.</p>}<p className="hint">Persistent project history and accounts are planned for a later release.</p></section>}
      {tab==="workspace" && <div className="workspace">
        <section className="canvas-area">
          <div className="panel-heading"><div><span className="eyebrow">EDITOR CANVAS</span><h2>{clip?clip.file.name:"Your video canvas"}</h2></div><div className="toggle-row"><button className={compare?"pill selected":"pill"} onClick={()=>setCompare(!compare)} disabled={!clip}><RotateCcw size={15}/> {compare?"Original view":"Compare"}</button></div></div>
          <div className="canvas" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();selectFile(e.dataTransfer.files[0]);}}>
            {clip ? <><video ref={video} src={clip.url} playsInline onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onTimeUpdate={e=>{const v=e.currentTarget;if(v.duration) setProgress(v.currentTime/v.duration*100);}} onEnded={()=>setPlaying(false)}/>{compare&&<div className="comparison-note">Original preview — enhanced comparison available after AI integration</div>}</> : <div className="dropzone"><div className="drop-icon"><UploadCloud size={35}/></div><h3>Drop your footage here</h3><p>Or import a video to open it on your canvas</p>{importButton}<small>MP4 • MOV • WEBM • MKV • AVI (browser playback depends on codec)</small></div>}
          </div>
          <div className="transport"><button onClick={playToggle} disabled={!clip}>{playing?<Pause size={18}/>:<Play size={18}/>}</button><span>{clip?"Video preview":"No media loaded"}</span><div className="timeline" onClick={e=>{if(!video.current?.duration)return;const r=e.currentTarget.getBoundingClientRect();video.current.currentTime=Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*video.current.duration;}}><div style={{width:progress+"%"}}/></div><span>{Math.round(progress)}%</span></div>
          <div className="bottom-panels"><div className="panel compact"><span className="eyebrow">SOURCE</span><strong>{clip?clip.file.name:"No source selected"}</strong><small>{clip?(clip.file.size/1024/1024).toFixed(2)+" MB":"Import footage to get started"}</small></div><div className="panel compact"><span className="eyebrow">OUTPUT</span><strong>{resolution} upscale</strong><small>{quality} • Configuration only</small></div></div>
        </section>
        <aside className="inspector"><div className="panel-heading"><div><span className="eyebrow">AI STUDIO</span><h2>Enhancement tools</h2></div><Settings2 size={20}/></div><div className="tool-group"><label>AI model</label><div className="tool-static"><WandSparkles size={18}/> Real-ESRGAN <small>Pending connection</small></div></div><div className="tool-group"><label>Output resolution</label><div className="choices">{["Original","2×","3×","4×"].map(x=><button key={x} className={resolution===x?"chosen":""} onClick={()=>setResolution(x)}>{x}</button>)}</div></div><div className="tool-group"><label>Enhancement mode</label><select value={quality} onChange={e=>setQuality(e.target.value)}><option>Standard</option><option>High Quality</option><option>Maximum Quality</option></select></div><div className="tool-group"><label>Processing mode</label><div className="tool-static"><Monitor size={18}/> Browser preview <small>Local AI: coming next</small></div></div><button className="primary wide" disabled={!clip} onClick={start}><WandSparkles size={18}/> Start Enhancement</button><button className="secondary wide" disabled={!clip} onClick={()=>setNotice("Enhanced export will be available when the processing engine is connected.")}><Download size={18}/> Export enhanced video</button><p className="hint">This first version previews original videos. It does not yet enhance or export processed files.</p></aside>
      </div>}
      {notice&&<div role="status" className="notice">{notice}<button onClick={()=>setNotice("")}>×</button></div>}
    </main>
    <input ref={input} type="file" accept=".mp4,.mov,.avi,.mkv,.webm,video/*" hidden onChange={e=>{selectFile(e.target.files?.[0]);e.target.value="";}}/>
  </div>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);
