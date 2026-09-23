import React, { useEffect, useRef, useState } from 'react'
import { ArrowUpRight, ArrowRight, FileText, Search, Layers3, Quote, History, AudioLines, BookOpen, Building2, ShieldCheck, NotebookText, GraduationCap, FolderKanban, Menu, X, Check } from 'lucide-react'
import './landing.css'

const features = [
  [Layers3, 'Retrieval-Augmented Generation', 'Your documents give the model its context. Relevant content comes first, so answers stay connected to the material you upload.'],
  [Search, 'Semantic Search', 'Find passages by meaning, even when your question uses different words from the original document.'],
  [FileText, 'Document Intelligence', 'Bring PDFs, Word documents, text, Markdown, HTML, CSV, and JSON into one question-and-answer workspace.'],
  [Quote, 'Source-Grounded Answers', 'Follow each answer back to its reference sources and preview the passages behind the response.'],
  [History, 'Conversation History', 'Return to previous conversations and keep asking with recent context from the same session.'],
  [AudioLines, 'Streaming AI Responses', 'Read answers as they arrive, with source references attached when the response is complete.'],
]
const steps = [
  ['Upload', 'Start with what you know.', 'Upload supported documents into your workspace. Select one file or ask across all of them.'],
  ['Process', 'Give your content structure.', 'Perinty extracts text, splits it into chunks, and creates vector embeddings.'],
  ['Retrieve', 'Find the relevant passages.', 'Your question is matched to meaningful passages stored in Supabase.'],
  ['Answer', 'Get an answer with context.', 'The language model streams a grounded answer with references to your documents.'],
]
const uses = [[BookOpen, 'Research documents'], [Building2, 'Company knowledge bases'], [ShieldCheck, 'Policy & compliance documents'], [NotebookText, 'Reports & manuals'], [GraduationCap, 'Academic materials'], [FolderKanban, 'Client & project documents']]

function WorkspacePreview() {
  const container = useRef(null)
  const [width, setWidth] = useState(1100)
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(container.current)
    return () => observer.disconnect()
  }, [])
  return <div className="lp-preview" ref={container}>
    <div className="lp-preview-bar"><span className="lp-window-dots"><i/><i/><i/></span><span>perinty / workspace</span><span className="lp-preview-label">REAL PRODUCT PREVIEW</span></div>
    <div className="lp-preview-body" style={{height: width * 930 / 1280}}>
      <iframe title="Preview of the existing Perinty document workspace" src="/app" tabIndex={-1} loading="lazy" aria-hidden="true" style={{width:1280,height:930,transform:`scale(${width / 1280})`}} />
      <a href="/app" className="lp-preview-cover" aria-label="Open the Perinty workspace"><span>Explore the workspace <ArrowUpRight size={16}/></span></a>
    </div>
  </div>
}

export default function LandingPage() {
  const [menu, setMenu] = useState(false)
  useEffect(() => { document.title = 'Perinty — AI Document Intelligence' }, [])
  return <div className="lp">
    <header className="lp-nav lp-wrap">
      <a className="lp-brand" href="/" aria-label="Perinty home"><span className="lp-logo"><Layers3 size={21}/></span>perinty<span className="lp-brand-dot">.</span></a>
      <nav className={menu ? 'lp-links is-open' : 'lp-links'} aria-label="Main navigation">
        {['Features', 'How It Works', 'Use Cases', 'Technology'].map(label => <a key={label} href={`#${label.toLowerCase().replaceAll(' ', '-')}`} onClick={() => setMenu(false)}>{label}</a>)}
      </nav>
      <a className="lp-button lp-button-small" href="/app">Try Perinty <ArrowUpRight size={16}/></a>
      <button className="lp-menu" aria-label={menu ? 'Close navigation' : 'Open navigation'} aria-expanded={menu} onClick={() => setMenu(!menu)}>{menu ? <X/> : <Menu/>}</button>
    </header>

    <main>
      <section className="lp-hero lp-wrap">
        <div className="lp-eyebrow"><span/> YOUR KNOWLEDGE. WITH CLARITY.</div>
        <div className="lp-hero-copy"><h1>Turn Your Documents<br/>Into <span>Answers.</span></h1><div className="lp-hero-aside"><p>Upload your documents and ask questions in natural language. Perinty uses retrieval-augmented generation to find the most relevant information and generate answers grounded in your content.</p><div className="lp-actions"><a className="lp-button" href="/app">Start Asking Questions <ArrowUpRight size={18}/></a><a className="lp-text-link" href="#how-it-works">See How It Works <ArrowRight size={16}/></a></div><p className="lp-demo-note">Explore the demo with non-sensitive documents.</p></div></div>
        <WorkspacePreview/>
        <div className="lp-preview-caption"><span><span className="lp-status-dot"/> The actual Perinty workspace. Ready to explore.</span><span>DOCUMENTS IN. UNDERSTANDING OUT.</span></div>
      </section>

      <section className="lp-value lp-wrap" aria-labelledby="value-heading"><div><span className="lp-eyebrow">LESS SEARCHING. MORE UNDERSTANDING.</span><h2 id="value-heading">A conversation with<br/>everything you’ve read.</h2></div><ul>{['Ask questions across uploaded documents', 'Get context-aware AI answers', 'Retrieve relevant document passages', 'View source references', 'Maintain conversation history', 'Work with multiple documents'].map(value => <li key={value}><Check size={17}/>{value}</li>)}</ul></section>

      <section className="lp-process" id="how-it-works"><div className="lp-wrap"><div className="lp-section-heading"><div><span className="lp-eyebrow">01 / HOW IT WORKS</span><h2>From file to clarity.<br/>In four simple steps.</h2></div><p>A thoughtful pipeline behind<br/>a simple conversation.</p></div><div className="lp-steps">{steps.map(([title, headline, text], i) => <article key={title}><div className="lp-step-number">0{i + 1}<ArrowRight size={20}/></div><h3>{title}</h3><strong>{headline}</strong><p>{text}</p></article>)}</div></div></section>

      <section className="lp-features lp-wrap" id="features"><div className="lp-section-heading"><div><span className="lp-eyebrow">02 / BUILT FOR YOUR KNOWLEDGE</span><h2>More than a chat box.<br/>A better way to work with documents.</h2></div></div><div className="lp-feature-grid">{features.map(([Icon, title, text]) => <article key={title}><div className="lp-feature-icon"><Icon size={23} strokeWidth={1.7}/></div><h3>{title}</h3><p>{text}</p></article>)}</div></section>

      <section className="lp-use-cases lp-wrap" id="use-cases"><div><span className="lp-eyebrow">03 / POSSIBILITIES</span><h2>For the documents<br/>that matter to you.</h2><p>Find the detail. Understand the context.<br/>Put what you know to work.</p><p className="lp-use-note">The current demo uses simulated identities. Try public or sample versions of these documents; private data requires real authentication.</p></div><div className="lp-use-grid">{uses.map(([Icon, title]) => <div key={title}><Icon size={21} strokeWidth={1.6}/><span>{title}</span><ArrowUpRight size={16}/></div>)}</div></section>

      <section className="lp-tech" id="technology"><div className="lp-wrap"><span className="lp-eyebrow">04 / UNDER THE HOOD</span><div className="lp-section-heading"><h2>Purpose-built.<br/>From interface to inference.</h2><p>A connected stack for turning document<br/>content into useful, grounded answers.</p></div><div className="lp-tech-grid">{[['React','The responsive workspace'],['FastAPI','The document & chat API'],['Supabase','Persistent knowledge & history'],['NVIDIA NIM','Language model inference'],['Vector embeddings','Meaning, made searchable'],['RAG','Context before generation']].map(([name, detail]) => <div key={name}><span>{name}</span><p>{detail}</p></div>)}</div></div></section>

      <section className="lp-final lp-wrap"><span className="lp-eyebrow">YOUR NEXT ANSWER STARTS HERE</span><h2>Your documents already<br/>contain the answers.<br/><span>Perinty helps you find them.</span></h2><a className="lp-button" href="/app">Open Perinty <ArrowUpRight size={18}/></a><p>No setup to explore. Bring a non-sensitive document.</p></section>
    </main>
    <footer className="lp-footer lp-wrap"><a className="lp-brand" href="/">perinty<span className="lp-brand-dot">.</span></a><span>AI Document Intelligence</span><span>© {new Date().getFullYear()} Perinty</span></footer>
  </div>
}
