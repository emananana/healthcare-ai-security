import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api } from './api';
import './style.css';

function Icon({ name = 'orbit', size = 22 }) {
  const paths = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
    policy: <><rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 8h8M8 12h8M8 16h4"/></>,
    claims: <><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z M9 8h6M9 12h6"/></>,
    chat: <><path d="M21 11a8 8 0 0 1-8 8H7l-4 3V11a9 9 0 0 1 18 0Z"/><path d="M8 10h8M8 14h5"/></>,
    shield: <><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/></>,
    attack: <><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 1v4m0 14v4M1 12h4m14 0h4"/></>,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6"/>,
    refresh: <><path d="M20 7a9 9 0 1 0 1 8M20 2v6h-6"/></>,
    star: <path d="m12 2 2.6 7.4L22 12l-7.4 2.6L12 22l-2.6-7.4L2 12l7.4-2.6L12 2Z"/>,
    orbit: <><circle cx="12" cy="12" r="6"/><ellipse cx="12" cy="12" rx="11" ry="4" transform="rotate(-35 12 12)"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.orbit}</svg>;
}
function Logo() {
  return <div className="brand"><span className="brand-mark"><Icon size={35}/></span><span>CometCare<span className="brand-tag">Your health is our universe.</span></span></div>;
}
function Badge({ value }) {
  const text = value ?? 'Pending';
  const tone = ['ALLOW', 'Allowed', 'low'].includes(text) ? 'good' : ['BLOCK', 'Denied', 'high'].includes(text) ? 'danger' : 'neutral';
  return <span className={`badge ${tone}`}>{text}</span>;
}
function Empty({ icon = 'orbit', title, children }) {
  return <div className="empty"><span className="icon-tile"><Icon name={icon} size={28}/></span><h3>{title}</h3><p>{children}</p></div>;
}
const memberNav = [['Overview', 'overview'], ['My Policy', 'policy'], ['My Claims', 'claims'], ['AI Assistant', 'chat']];
const labNav = [['Attack Simulator', 'attack'], ['Defense Analysis', 'shield'], ['Audit Log', 'claims']];
const time = value => { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString(); };

function App() {
  const [users, setUsers] = useState([]);
  const [runtime, setRuntime] = useState(null);
  const [customerId, setCustomerId] = useState('');
  const [events, setEvents] = useState([]);
  const [history, setHistory] = useState({});
  const [records, setRecords] = useState({});
  const [message, setMessage] = useState('');
  const [attack, setAttack] = useState(null);
  const [mode, setMode] = useState('member');
  const [page, setPage] = useState('Overview');
  const [busy, setBusy] = useState('Loading your demo');
  const [error, setError] = useState('');
  const chatEnd = useRef(null);
  const user = users.find(item => item.customer_id === customerId);
  const target = users.find(item => item.customer_id !== customerId);
  const conversation = history[customerId] || [];
  const memberRecords = records[customerId] || {};
  const lab = mode === 'lab';
  const disabled = !!busy || !customerId;

  async function load() {
    setBusy('Refreshing demo data'); setError('');
    try {
      const [nextUsers, nextEvents, nextRuntime] = await Promise.all([api.users(), api.events(), api.status()]);
      setRuntime(nextRuntime);
      setUsers(nextUsers); setCustomerId(current => nextUsers.some(u => u.customer_id === current) ? current : nextUsers[0]?.customer_id || '');
      setEvents(nextEvents);
    } catch (err) { setError(err.message); }
    finally { setBusy(''); }
  }
  useEffect(() => { load(); }, []);
  useEffect(() => { if (page === 'AI Assistant') chatEnd.current?.scrollIntoView({ block: 'nearest' }); }, [conversation.length, page, busy]);
  async function act(label, operation) {
    if (busy) return;
    setBusy(label); setError('');
    try { await operation(); } catch (err) { setError(err.message); } finally { setBusy(''); }
  }
  function addEvent(event) {
    setEvents(previous => [...previous.filter(item => item.event_id !== event.event_id), event]);
  }
  function switchMode(next) { setMode(next); setPage(next === 'member' ? 'Overview' : 'Attack Simulator'); }
  async function fetchRecord(resource) {
    await act(`Retrieving your ${resource}`, async () => {
      const response = await api.chat(customerId, `Show my ${resource}`);
      setRecords(previous => ({ ...previous, [customerId]: { ...previous[customerId], [resource]: response } }));
      addEvent(response.event);
    });
  }
  async function send(event) {
    event.preventDefault();
    if (!message.trim() || disabled) return;
    await act('CometCare is responding', async () => {
      const response = await api.chat(customerId, message);
      setHistory(previous => ({ ...previous, [customerId]: [...(previous[customerId] || []), { question: message, response }] }));
      addEvent(response.event); setMessage('');
    });
  }
  function recordPage(resource) {
    const response = memberRecords[resource];
    return <div className="two-column"><section className="card record-card">
      <div className="section-heading"><span className="icon-tile"><Icon name={resource === 'policy' ? 'policy' : 'claims'}/></span><div><h2>{resource === 'policy' ? 'Your policy, at a glance' : 'Your claims'}</h2><p>For {user?.display_name || 'your demo membership'}</p></div></div>
      {response ? <div className="record-content"><div className="eyebrow">{response.event.outcome === 'ALLOW' ? 'Retrieved from your synthetic record' : 'Request response'}</div><p className="record-text">{response.message}</p><small>Retrieved {time(response.event.timestamp)}</small></div> : <Empty icon={resource === 'policy' ? 'policy' : 'claims'} title={`Your ${resource} information is one click away`}>Retrieve your available synthetic record securely through the CometCare assistant.</Empty>}
      <button className="primary" disabled={disabled} onClick={() => fetchRecord(resource)}>{response ? 'Refresh information' : `View my ${resource}`}<Icon name="arrow" size={18}/></button>
    </section><aside className="card soft"><Icon name="chat" size={28}/><h2>A little clarity goes a long way.</h2><p>Need help finding your policy or claims? Ask the CometCare assistant.</p><button className="text-button" onClick={() => setPage('AI Assistant')}>Talk to the assistant <Icon name="arrow" size={17}/></button><div className="divider"/><small>This demo provides a text summary only. {resource === 'policy' ? 'Coverage limits, deductibles, and policy documents are not available.' : 'Itemized claims, documents, and a payment timeline are not available.'}</small></aside></div>;
  }

  return <div className={`app-shell ${lab ? 'lab-mode' : ''}`}>
    <a className="skip-link" href="#content">Skip to content</a>
    <aside className="sidebar">
      <Logo/>
      <div className="workspace-switch" aria-label="Workspace"><button aria-pressed={!lab} onClick={() => switchMode('member')}>Member Portal</button><button aria-pressed={lab} onClick={() => switchMode('lab')}>Security Lab</button></div>
      <div className="nav-label">{lab ? 'RESEARCH WORKSPACE' : 'YOUR COMETCARE'}</div>
      <nav aria-label={lab ? 'Security Lab' : 'Member Portal'}>{(lab ? labNav : memberNav).map(([name, icon]) => <button key={name} aria-current={page === name ? 'page' : undefined} onClick={() => setPage(name)}><Icon name={icon}/>{name}{page === name && <span className="nav-dot"/>}</button>)}</nav>
      <div className="sidebar-note"><Icon name={lab ? 'shield' : 'star'}/><h3>{lab ? 'A safe space to test.' : 'Care in your orbit.'}</h3><p>{lab ? 'Explore how simulated requests move through layered defenses.' : 'Your policy, claims, and a little guidance. All in one place.'}</p></div>
      <div className="sidebar-bottom"><span className="demo-dot"/> Synthetic Demo<p>Fictional insurance company.<br/>Not an official UT Dallas service.</p></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb">CometCare <span>/</span> <strong>{lab ? 'Security Lab' : 'Member Portal'}</strong></div><div className="identity"><span className="avatar">{user?.display_name?.charAt(0) || 'C'}</span><label><span>Demo member</span><select aria-label="Select demo customer" value={customerId} disabled={!!busy || !users.length} onChange={event => { setCustomerId(event.target.value); setMessage(''); setAttack(null); setError(''); }}>{!users.length && <option value="">No members loaded</option>}{users.map(u => <option key={u.customer_id} value={u.customer_id}>{u.display_name} · {u.customer_id}</option>)}</select></label></div></header>
      <main id="content" tabIndex="-1">
        <div className="page-heading"><div><div className="eyebrow">{lab ? 'COMETCARE / SECURITY RESEARCH' : 'A LITTLE PEACE OF MIND'}</div><h1>{page === 'Overview' ? `Welcome, ${user?.display_name || 'stargazer'}.` : page}</h1><p>{lab ? 'Controlled simulations. Clear decisions. Better understanding.' : page === 'Overview' ? 'Let’s make looking after your health feel a little simpler.' : 'Your health is our universe.'}</p></div><span className="demo-label"><span className="demo-dot"/> Synthetic Demo</span></div>
        {runtime && <p className="muted">Assistant: {runtime.enterprise_mode === 'live' ? `Live Groq · ${runtime.enterprise_model}` : 'Mock (no LLM calls)'} · Red team: {runtime.red_mode} · Blue team: {runtime.blue_mode}</p>}
        {busy && <div className="status" role="status"><span className="spinner"/>{busy}…</div>}
        {error && <div className="error" role="alert"><strong>We couldn’t complete that request.</strong><p>{error}</p><button className="secondary" onClick={load} disabled={!!busy}>Reconnect & refresh</button></div>}
        {!busy && !users.length && !error && <Empty title="No demo members available">A demo member is needed to retrieve records or send a request. <button className="text-button" onClick={load}>Refresh demo</button></Empty>}

        {page === 'Overview' && <>
          <section className="hero"><div className="hero-copy"><span className="eyebrow">WELCOME TO YOUR MEMBER PORTAL</span><h2>A healthier world.<br/>In your orbit.</h2><p>A simple place to find your insurance information and get a little guidance along the way.</p><button className="cream-button" onClick={() => setPage('AI Assistant')}>Meet your assistant <Icon name="arrow" size={18}/></button></div><div className="orbit-art" aria-hidden="true"><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="planet"><span>+</span></div><span className="orbit-moon"/><span className="spark spark-one">✦</span><span className="spark spark-two">✧</span><span className="orbit-caption">A LITTLE CARE GOES A LONG WAY</span></div></section>
          <div className="overview-grid"><section className="card membership"><div className="card-heading"><h2>Your membership</h2><Icon name="orbit"/></div><div className="member-name">{user?.display_name || 'Select a demo member'}</div><div className="member-fields"><div><span>Demo member ID</span><strong>{customerId || 'Not selected'}</strong></div><div><span>Record environment</span><strong>Synthetic</strong></div></div><div className="membership-footer">CometCare <span>MEMBER PORTAL</span></div></section>
          <section className="card"><div className="card-heading"><h2>Policy snapshot</h2><Icon name="policy"/></div><p>{memberRecords.policy?.event.outcome === 'ALLOW' ? memberRecords.policy.message : 'Your policy information, straight from the available demo record.'}</p><button className="text-button" onClick={() => setPage('My Policy')}>View policy details <Icon name="arrow" size={17}/></button><small className="block">No policy status is assumed until your record is retrieved.</small></section></div>
          <div className="section-title"><h2>How can we help today?</h2><span>YOUR NEXT STEP, MADE SIMPLE</span></div>
          <div className="quick-grid">{[['My Policy', 'policy', 'Know your policy', 'Find your available plan information.'], ['My Claims', 'claims', 'Check your claims', 'See what’s in your synthetic claim record.'], ['AI Assistant', 'chat', 'Let’s talk', 'Ask a question about your policy or claims.']].map(([name, icon, title, description]) => <button className="quick-card" key={name} onClick={() => setPage(name)}><span className="icon-tile"><Icon name={icon}/></span><h3>{title}</h3><p>{description}</p><span className="quick-arrow"><Icon name="arrow" size={19}/></span></button>)}</div>
          <div className="care-note"><Icon name="star"/><div><strong>A clearer view of your care.</strong><p>This fictional portal helps you explore insurance information using synthetic records only.</p></div></div>
        </>}
        {page === 'My Policy' && recordPage('policy')}
        {page === 'My Claims' && recordPage('claims')}
        {page === 'AI Assistant' && <div className="assistant-layout"><section className="card chat-card"><div className="chat-header"><span className="assistant-avatar"><Icon/></span><div><h2>CometCare Assistant</h2><p>Your guide to synthetic policy & claim records</p></div><span className="badge neutral">Demo</span></div><div className="chat-messages" role="log" aria-label="Conversation"><div className="bubble assistant"><span className="message-author">COMETCARE</span><p>Hello! I can help you find your own policy information or claims. What would you like to explore?</p></div>{conversation.map(({ question, response }) => <React.Fragment key={response.event.event_id}><div className="bubble customer"><span className="message-author">YOU</span><p>{question}</p></div><div className="bubble assistant"><span className="message-author">COMETCARE</span><p>{response.message}</p></div></React.Fragment>)}{busy === 'CometCare is responding' && <div className="typing">Finding your answer…</div>}<div ref={chatEnd}/></div><form className="chat-form" onSubmit={send}><label className="sr-only" htmlFor="message">Ask the CometCare assistant</label><textarea id="message" placeholder="Ask about your policy or claims…" value={message} onChange={event => setMessage(event.target.value)} maxLength={4000} required disabled={disabled}/><div className="composer-bottom"><small>Synthetic records only. No medical advice.</small><button className="primary" disabled={disabled || !message.trim()}>Send <Icon name="arrow" size={17}/></button></div></form></section><aside><section className="card"><span className="icon-tile"><Icon name="star"/></span><h2>A good place to start</h2><p>Choose a question, then send it to your assistant.</p>{['Show my policy', 'Show my claims'].map(question => <button className="prompt" disabled={disabled} key={question} onClick={() => { setMessage(question); document.getElementById('message')?.focus(); }}>{question}<Icon name="arrow" size={16}/></button>)}</section><div className="aside-note"><Icon name="shield"/><p>Your request passes through the simulation’s security checks before a record is returned.</p></div></aside></div>}

        {lab && <div className="lab-notice"><Icon name="shield" size={18}/><span>Team research workspace · All browser clients share the API audit log. Backend restarts clear it. Demo identity selection is not authentication.</span></div>}
        {page === 'Attack Simulator' && <div className="two-column"><section className="card"><div className="section-heading"><span className="icon-tile orange"><Icon name="attack"/></span><div><h2>Cross-member access test</h2><p>One request. Two layers of defense.</p></div></div><p>Test how the assistant responds when one demo member requests another member’s claims. The existing red agent generates the request; no new attack logic runs in this interface.</p><div className="test-route"><div><span>Requesting member</span><strong>{customerId || '—'}</strong></div><Icon name="arrow"/><div><span>Target member</span><strong>{target?.customer_id || 'Unavailable'}</strong></div></div><button className="primary" disabled={disabled || !target} onClick={() => act('Running simulation', async () => { const result = await api.attack(customerId, target.customer_id); setAttack(result); addEvent(result.response.event); })}><Icon name="attack" size={18}/>Run simulated attack</button></section><section className="card soft"><h2>What are we testing?</h2><ol className="steps"><li><strong>Generate a request</strong><p>The red agent asks for another member’s synthetic data.</p></li><li><strong>Evaluate & authorize</strong><p>The blue agent recommends a response. The gateway makes a separate access decision.</p></li><li><strong>Inspect the outcome</strong><p>The enterprise agent responds and records the event.</p></li></ol></section><section className="card full-width"><div className="card-heading"><h2>Latest simulation result</h2>{attack && <Badge value={attack.response.event.outcome}/>}</div>{attack ? <><div className="result-pair"><div><div className="eyebrow">GENERATED ATTACK · {attack.attack.category}</div><p>{attack.attack.message}</p></div><div><div className="eyebrow">ASSISTANT RESPONSE</div><p>{attack.response.message}</p></div></div><button className="text-button" onClick={() => setPage('Defense Analysis')}>Inspect defense analysis <Icon name="arrow" size={17}/></button></> : <Empty icon="attack" title="Ready when you are">Run a simulation to see the actual generated prompt, response, and outcome here.</Empty>}</section></div>}
        {page === 'Defense Analysis' && <><div className="lab-summary">{[['Observed events', events.length], ['Final BLOCK outcomes', events.filter(e => e.outcome === 'BLOCK').length], ['Final ALLOW outcomes', events.filter(e => e.outcome === 'ALLOW').length]].map(([label, count]) => <div className="card" key={label}><span>{label}</span><strong>{count}</strong></div>)}</div><div className="section-title"><h2>Decision breakdown</h2><button className="text-button" disabled={!!busy} onClick={load}><Icon name="refresh" size={16}/>Refresh events</button></div><p className="muted">Recommendations are not final outcomes. DECEIVE currently blocks access; there is no standalone blue-team action.</p>{!events.length && <section className="card"><Empty icon="shield" title="No decisions to review yet">Run an attack or make a member request. Its actual decisions will appear here.</Empty></section>}{[...events].reverse().map(event => <section className="card defense-event" key={event.event_id}><div className="card-heading"><span className="event-meta">{event.user.customer_id} · {event.source === 'red_team' ? 'Red team' : 'Member request'} · {time(event.timestamp)}</span><Badge value={event.outcome}/></div><h3>{event.message}</h3><div className="decision-grid"><div><div className="eyebrow">01 / BLUE-TEAM RECOMMENDATION</div><div className="badges"><Badge value={event.defense?.recommendation}/><span>Risk: <Badge value={event.defense?.risk}/></span></div><p>{event.defense?.reason || 'No analysis returned.'}</p></div><div><div className="eyebrow">02 / TRADITIONAL AUTHORIZATION</div><Badge value={event.authorization ? event.authorization.allowed ? 'Allowed' : 'Denied' : null}/><p>{event.authorization?.reason || 'No authorization returned.'}</p></div><div><div className="eyebrow">03 / FINAL OUTCOME</div><Badge value={event.outcome}/><p>{event.outcome === 'BLOCK' ? 'The request was blocked.' : event.outcome === 'ALLOW' ? 'The request was allowed.' : 'No final outcome yet.'} {event.defense?.recommendation === 'BLOCK' ? 'The blue agent recommended blocking.' : 'Review the recommendation separately from authorization.'}</p></div></div><small className="event-id">Event {event.event_id}</small></section>)}</>}
        {page === 'Audit Log' && <section className="card audit-card"><div className="card-heading"><div><h2>Activity timeline</h2><p>{events.length} recorded events · newest first</p></div><button className="secondary" disabled={!!busy} onClick={load}><Icon name="refresh" size={16}/>Refresh</button></div>{!events.length ? <Empty icon="claims" title="A fresh start">Chat requests, record retrievals, and simulated attacks will appear here after execution.</Empty> : <div className="table-scroll"><table><caption className="sr-only">Actual simulation audit events</caption><thead><tr><th>Time / member</th><th>Request / source</th><th>Blue team</th><th>Authorization</th><th>Outcome</th></tr></thead><tbody>{[...events].reverse().map(event => <tr key={event.event_id}><td><time dateTime={event.timestamp}>{time(event.timestamp)}</time><small>{event.user.customer_id}</small></td><td><span className="table-message">{event.message}</span><small>{event.source} · {event.action.resource} → {event.action.customer_id}</small><details><summary>Event details</summary><pre>{JSON.stringify(event, null, 2)}</pre></details></td><td><Badge value={event.defense?.recommendation}/><small>Risk: {event.defense?.risk || 'Pending'}</small></td><td><Badge value={event.authorization ? event.authorization.allowed ? 'Allowed' : 'Denied' : null}/></td><td><Badge value={event.outcome}/></td></tr>)}</tbody></table></div>}</section>}
        <footer><span>CometCare <span className="footer-star">✦</span> Your health is our universe.</span><span>Fictional university project. Not affiliated with UT Dallas.</span></footer>
      </main>
    </div>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
