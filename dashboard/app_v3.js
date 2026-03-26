// ─── HKJC AI — Race Day Dashboard v4 ────────────────────────────────────────
const API = (() => {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') return 'http://localhost:8000';
    if (host === 'hkjc-predictor-v3.web.app' || host === 'hkjc-predictor-v3.firebaseapp.com') {
        return 'https://hkjc-predictor-mj2mcbfjxq-uc.a.run.app';
    }
    return window.location.origin;
})();

const POLL_MS = 5000;

// State
let allPicks      = [];   // [{race_no, horse_no, horse_name, prob, kelly_stake, market_odds, is_best_bet, race_id}]
let allPredictions= {};   // race_id -> full prediction object (loaded on demand)
let currentRaceNo = null;
let currentRaceId = null;
let meetingDate   = '';
let meetingVenue  = '';
let lastHash      = '';

// ─── CLOCK ───────────────────────────────────────────────────────────────────
function tickClock() {
    const d = new Date();
    document.getElementById('clock').textContent = d.toTimeString().slice(0, 8);
}
tickClock();
setInterval(tickClock, 1000);

// ─── UTILS ───────────────────────────────────────────────────────────────────
function formatDate(dateStr) {
    if (!dateStr) return '';
    const [y, m, d] = dateStr.split('-');
    const date = new Date(y, m - 1, d);
    return date.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

// ─── FAB REFRESH ─────────────────────────────────────────────────────────────
document.getElementById('fab-refresh').addEventListener('click', async () => {
    const fab = document.getElementById('fab-refresh');
    fab.classList.add('spinning');
    fab.style.pointerEvents = 'none';
    try {
        await fetch(`${API}/execution/force_update`, { method: 'POST' });
        lastHash = ''; // force re-render
        await poll();
    } catch(e) {
        console.error('Force update failed:', e);
    } finally {
        fab.classList.remove('spinning');
        fab.style.pointerEvents = '';
    }
});

// ─── MAIN POLL ───────────────────────────────────────────────────────────────
async function poll() {
    try {
        // Fetch picks + weather/health in parallel
        const [picksResp, latestResp] = await Promise.all([
            fetch(`${API}/picks/upcoming`),
            fetch(`${API}/latest?t=${Date.now()}`)
        ]);

        const picksData  = await picksResp.json();
        const latestData = await latestResp.json();

        setConnected(true);

        if (picksData.success && picksData.picks?.length) {
            allPicks    = picksData.picks;
            
            // Update Bankroll Display
            if (picksData.bankroll) {
                const bankrollEl = document.getElementById('topbar-bankroll');
                const wrap = document.getElementById('topbar-bankroll-wrap');
                if (bankrollEl && wrap) {
                    bankrollEl.textContent = '$' + picksData.bankroll.toLocaleString();
                    wrap.style.display = 'flex';
                }
            }

            // Robust Date/Venue detection
            meetingDate = picksData.date || allPicks[0]?.race_id?.split('_')[0] || '';
            meetingVenue= allPicks[0]?.race_id?.split('_')[1] || '';
            
            console.log(`[Dashboard] Meeting: ${meetingDate} (${meetingVenue})`);
            renderVenueHeader();
            renderRaceTabs();
        }

        if (latestData.success) {
            renderWeather(latestData.weather);
            renderAlerts(latestData.alerts?.alerts || []);
            renderCloudSync(latestData.health?.services?.cloud_sync);
        }

        if (latestData.success || picksData.success) {
            const loader = document.getElementById('loading-state');
            if (loader) loader.style.display = 'none';
        }

        // Hash change check (avoid flashing if nothing changed)
        const hash = `${allPicks.map(p=>p.kelly_stake).join(',')}|${latestData.weather?.track_condition_forecast}`;
        if (hash !== lastHash) {
            lastHash = hash;

            // Auto-select Overview on first load
            if (currentRaceNo === null && allPicks.length) {
                selectRace('all');
            } else if (currentRaceNo !== null) {
                // Re-render currently selected race with fresh data
                await renderRaceDetail(currentRaceNo);
            }
        }

    } catch(e) {
        setConnected(false);
        console.error('Poll error:', e);
    }
}

function setConnected(ok) {
    const dot = document.getElementById('health-dot');
    if (!dot) return;
    dot.className = 'dot' + (ok ? '' : ' err');
    dot.title = ok ? 'Connected' : 'Disconnected';
}

// ─── VENUE / DATE HEADER ─────────────────────────────────────────────────────
function renderVenueHeader() {
    const venueMap = { ST: 'SHA TIN', HV: 'HAPPY VALLEY' };
    document.getElementById('topbar-venue').textContent = venueMap[meetingVenue] || meetingVenue || 'MEETING';
    document.getElementById('topbar-date').textContent = formatDate(meetingDate);
}

// ─── RACE TABS ───────────────────────────────────────────────────────────────
function renderRaceTabs() {
    const container = document.getElementById('race-tabs');
    const maxRace   = Math.max(...allPicks.map(p => p.race_no));

    // Only rebuild if count differs
    if (container.children.length === maxRace) return;

    container.innerHTML = '';
    
    // 0. All Races / Summary Tab
    const allBtn = document.createElement('button');
    allBtn.className = 'race-tab' + (currentRaceNo === 'all' ? ' active' : '');
    allBtn.id = 'tab-all';
    allBtn.textContent = 'MEETING';
    allBtn.onclick = () => selectRace('all');
    container.appendChild(allBtn);

    for (let r = 1; r <= maxRace; r++) {
        const pick = allPicks.find(p => p.race_no === r);
        const hasStake = pick && (pick.kelly_stake > 0 || (pick.kelly_selections && pick.kelly_selections.length > 0));
        const btn = document.createElement('button');
        btn.className = 'race-tab' + (hasStake ? ' has-stake' : '') + (r === currentRaceNo ? ' active' : '');
        btn.id = `tab-R${r}`;
        btn.textContent = `R${r}`;
        btn.onclick = () => selectRace(r);
        container.appendChild(btn);
    }
}

function setActiveTab(raceNo) {
    document.querySelectorAll('.race-tab').forEach(t => t.classList.remove('active'));
    const tab = document.getElementById(`tab-R${raceNo}`);
    if (tab) {
        tab.classList.add('active');
        tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
}

// ─── RACE SELECTION ───────────────────────────────────────────────────────────
async function selectRace(raceNo) {
    currentRaceNo = raceNo;
    setActiveTab(raceNo);
    if (raceNo === 'all') {
        renderMeetingOverview();
    } else {
        await renderRaceDetail(raceNo);
    }
}

async function renderRaceDetail(raceNo) {
    const pick = allPicks.find(p => p.race_no === raceNo);
    if (!pick) return;

    const raceId = pick.race_id || `${meetingDate}_${meetingVenue}_R${raceNo}`;
    currentRaceId = raceId;

    // Load full prediction if not cached
    if (!allPredictions[raceId]) {
        try {
            const resp = await fetch(`${API}/prediction/${raceId}`);
            const data = await resp.json();
            if (data.success) allPredictions[raceId] = data.prediction;
        } catch(e) { console.warn('Could not load full prediction:', e); }
    }

    const pred   = allPredictions[raceId];
    const alerts = window._lastAlerts || [];

    renderMain(pick, pred, alerts);
}

// ─── MAIN CONTENT RENDERER ───────────────────────────────────────────────────
function renderMain(pick, pred, alerts) {
    const main = document.getElementById('main-content');

    // ── Bet Card ──
    const hasStake   = pick.kelly_stake > 0;
    const bankrollPct= pick.kelly_stake ? ((pick.kelly_stake / 10000) * 100).toFixed(1) : null;
    const confPct    = Math.round((pick.prob || 0) * 100);
    const odds       = pick.market_odds > 0 ? `${pick.market_odds}×` : '--';
    const badgeHtml  = hasStake
        ? `<div class="best-bet-badge">★ KELLY BET RECOMMENDED</div>`
        : `<div class="watch-badge">👁 WATCH RACE</div>`;

    // ── All Kelly selections for this race ──
    const kellySels = pick.kelly_selections || (hasStake ? [{ horse_no: pick.horse_no, kelly_stake: pick.kelly_stake, market_odds: pick.market_odds }] : []);
    // Build kelly rows separately to avoid nested template literal issues
    let kellyRowsHtml = '';
    if (kellySels.length > 1) {
        const rows = kellySels.map(function(sel) {
            const pct = ((sel.kelly_stake / 10000) * 100).toFixed(1);
            const o   = sel.market_odds > 0 ? sel.market_odds + '×' : '--';
            const horseName = sel.horse_name
                || (pred && pred.horse_names && pred.horse_names[sel.horse_no])
                || 'Horse ' + sel.horse_no;
            return '<div class="runner-row" style="padding:10px 0">'
                + '<div class="runner-no top">' + sel.horse_no + '</div>'
                + '<div class="runner-name" style="color:var(--green);font-weight:700">★ ' + horseName + ' · Kelly $' + sel.kelly_stake
                + ' <span style="color:var(--muted);font-weight:400">(' + pct + '% bankroll · ' + o + ')</span></div>'
                + '<button class="btn btn-stage" style="flex:0 0 auto;padding:6px 14px;font-size:11px" onclick="stageBetHorse(\'' + sel.horse_no + '\', ' + sel.kelly_stake + ')">STAGE</button>'
                + '</div>';
        });
        kellyRowsHtml = '<div class="section-label" style="margin-top:14px">All Bets This Race</div>' + rows.join('');
    }

    // ── Runner list ──
    let runnersHtml = '';
    if (pred?.probabilities) {
        // Top 6 by probability …
        const top6 = Object.entries(pred.probabilities).sort(([,a],[,b]) => b - a).slice(0, 6);
        // … plus any Kelly horses not already in top 6
        const top6ids = new Set(top6.map(([id]) => id));
        const extraKelly = kellySels
            .filter(s => !top6ids.has(s.horse_no))
            .map(s => [s.horse_no, pred.probabilities[s.horse_no] || 0]);
        const rows = [...top6, ...extraKelly];
        const topProb = top6[0]?.[1] || 1;
        runnersHtml = rows.map(([id, prob]) => {
            const pct   = Math.round((prob || 0) * 100);
            const hasK  = kellySels.some(s => s.horse_no === id);
            const name  = pred.horse_names?.[id] || ('#' + id);
            const barW  = Math.round(((prob || 0) / topProb) * 100);
            const barCol= hasK ? 'var(--green)' : 'var(--muted2)';
            const label = hasK ? ' ★' : '';
            return `
            <div class="runner-row">
              <div class="runner-no ${hasK ? 'top' : ''}">${id}</div>
              <div class="runner-name" ${hasK ? 'style="color:var(--text);font-weight:700"' : ''}>${name}${label}</div>
              <div class="runner-bar-bg"><div class="runner-bar-fill" style="width:${barW}%;background:${barCol}"></div></div>
              <div class="runner-prob" style="${hasK ? 'color:var(--green)' : ''}">${pct}%</div>
            </div>`;
        }).join('');
    }

    // ── Alerts pills ──
    let alertsHtml = '';
    const raceAlerts = alerts.filter(a => a.race_no === pick.race_no || !a.race_no).slice(0, 3);
    if (raceAlerts.length || alerts.length) {
        const displayAlerts = raceAlerts.length ? raceAlerts : alerts.slice(0, 3);
        alertsHtml = displayAlerts.map(a => {
            const isSmart = a.type === 'SMART MONEY' || a.severity === 'high';
            return `<div class="alert-pill ${isSmart?'smart':'info'}"><div class="alert-dot"></div>${a.type || 'SIGNAL'} — ${a.description || a.horse_no || ''}</div>`;
        }).join('');
    }

    // ── Analysis ──
    const analysisText = pred?.analysis_markdown || 'No AI analysis available for this race yet.';
    const analysisHtml = analysisText
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');

    const rankOfRunners = pred ? Object.keys(pred.probabilities || {}).length : '--';

    main.innerHTML = `
    <!-- BET CARD -->
    <div class="bet-card">
      ${badgeHtml}
      <div class="horse-row">
        <div class="horse-num">${pick.horse_no}<small>WIN</small></div>
        <div class="horse-info">
          <div class="horse-name">${pick.horse_name || `Horse #${pick.horse_no}`}</div>
          <div class="horse-meta" id="horse-meta-line">Race ${pick.race_no} &middot; AI Top Pick</div>
        </div>
      </div>
      <div class="prob-section">
        <div class="prob-label-row">
          <div>AI Win Probability</div>
          <div><strong>${confPct}%</strong> confidence</div>
        </div>
        <div class="prob-bar-bg"><div class="prob-bar-fill" style="width:${confPct}%"></div></div>
      </div>
      <div class="stats-row">
        <div class="stat-box">
          <div class="stat-label">Kelly Stake</div>
          <div class="stat-value ${hasStake?'green':'muted'}">${hasStake ? '$'+pick.kelly_stake : 'NO BET'}</div>
          <div class="stat-sub">${bankrollPct ? bankrollPct+'% bankroll' : 'No odds scraped'}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Market Odds</div>
          <div class="stat-value gold">${odds}</div>
          <div class="stat-sub">${hasStake ? 'EV positive' : pick.has_odds ? 'Odds available' : 'Not yet scraped'}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Bets This Race</div>
          <div class="stat-value blue">${kellySels.length || '--'}</div>
          <div class="stat-sub">of ${rankOfRunners} runners</div>
        </div>
      </div>
      ${kellyRowsHtml}
      <div style="display:flex;gap:8px;margin-top:14px">
        <button class="btn btn-stage" id="stage-btn" onclick="stageBet()">&#9889; STAGE BET</button>
        <button class="btn btn-copy" onclick="copyBet()">&#128203; COPY</button>
      </div>
    </div>


    ${alertsHtml ? `
    <div class="section-label">Market Signals</div>
    <div class="alerts-row">${alertsHtml}</div>` : ''}

    ${runnersHtml ? `
    <div class="runners-section">
      <div class="section-label">Race ${pick.race_no} — Top Runners</div>
      ${runnersHtml}
    </div>` : ''}

    <button class="analysis-toggle" id="analysis-toggle" onclick="toggleAnalysis()">
      <span>▾ AI Reasoning — Gemini 1.5 Flash</span>
      <span class="analysis-arrow">▾</span>
    </button>
    <div class="analysis-body" id="analysis-body">${analysisHtml}</div>
    `;

    // Populate racecard meta if available
    populateHorseMeta(pick, pred);
}

// ─── MEETING OVERVIEW RENDERER ───────────────────────────────────────────────
function renderMeetingOverview() {
    const main = document.getElementById('main-content');
    
    let rowsHtml = allPicks.map(p => {
        const hasRaceStake = p.kelly_stake > 0 || (p.kelly_selections && p.kelly_selections.length > 0);
        const hasStake = p.kelly_stake > 0;
        const probPct  = Math.round((p.prob || 0) * 100);
        const name     = p.horse_name || `Horse #${p.horse_no}`;
        const odds     = p.market_odds > 0 ? `${p.market_odds}×` : '--';
        
        return `
        <div class="runner-row" style="cursor:pointer; padding: 12px 16px; border-bottom: 1px solid var(--border)" onclick="selectRace(${p.race_no})">
            <div style="flex: 0 0 40px; font-weight: 800; color: var(--gold)">R${p.race_no}${hasRaceStake ? '★' : ''}</div>
            <div class="runner-no ${hasStake ? 'top' : ''}" style="flex: 0 0 30px">${p.horse_no}</div>
            <div class="runner-name" style="flex: 1; ${hasStake ? 'color:var(--text); font-weight:700' : ''}">${name}${p.is_best_bet ? ' ★' : ''}</div>
            <div style="flex: 0 0 60px; text-align: right; color: var(--gold)">${odds}</div>
            <div style="flex: 0 0 60px; text-align: right; font-weight: 700; color: ${hasStake ? 'var(--green)' : 'var(--text)'}">${probPct}%</div>
            <div style="flex: 0 0 80px; text-align: right; font-weight: 800; color: var(--green)">${hasStake ? '$'+Math.round(p.kelly_stake) : ''}</div>
        </div>`;
    }).join('');

    main.innerHTML = `
    <div class="runners-section" style="margin-top: 0; border-radius: 12px; overflow: hidden">
        <div class="section-label" style="background: var(--bg-card); margin: 0; padding: 16px; border-bottom: 1px solid var(--border)">
            Meeting Summary — Top AI Picks
        </div>
        <div style="display: flex; padding: 8px 16px; font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; background: var(--bg-dark)">
            <div style="flex: 0 0 40px">Race</div>
            <div style="flex: 0 0 30px">#</div>
            <div style="flex: 1">Top Runner</div>
            <div style="flex: 0 0 60px; text-align: right">Odds</div>
            <div style="flex: 0 0 60px; text-align: right">Conf</div>
            <div style="flex: 0 0 80px; text-align: right">Kelly</div>
        </div>
        <div style="background: var(--bg-card)">
            ${rowsHtml || '<div style="padding: 20px; text-align: center; color: var(--muted)">No predictions loaded yet.</div>'}
        </div>
    </div>
    <div style="margin-top: 20px; padding: 16px; background: rgba(255,193,7,0.05); border: 1px solid rgba(255,193,7,0.2); border-radius: 12px; font-size: 12px; color: var(--muted)">
        <strong>How to use:</strong> This overview shows the single highest-probability horse for each race. 
        Click on any row to view the full race analysis, market signals, and alternative betting options.
        <div style="margin-top: 10px; opacity: 0.5; font-size: 10px; text-align: right">Build v2026.03.26.1925 (Dashboard Restoration)</div>
    </div>
    `;
}

function populateHorseMeta(pick, pred) {
    const metaEl = document.getElementById('horse-meta-line');
    if (!metaEl) return;

    // Try to pull jockey/trainer from racecard
    const parts = [];
    parts.push(`Race ${pick.race_no}`);
    if (pred?.race_class) parts.push(pred.race_class);
    if (pick.market_odds > 0) parts.push(`Odds ${pick.market_odds}×`);
    metaEl.textContent = parts.join(' · ');
}

// ─── WEATHER ─────────────────────────────────────────────────────────────────
function renderWeather(w) {
    if (!w) return;
    document.getElementById('tw-track').textContent = w.track_condition_forecast || 'Good';
    document.getElementById('tw-rain').textContent  = w.prob_rain != null ? Math.round(w.prob_rain*100)+'%' : '--%';
    document.getElementById('tw-heat').textContent  = w.prob_temp_above_30 != null ? Math.round(w.prob_temp_above_30*100)+'%' : '--%';
}

// ─── ALERTS (store globally for race detail rerender) ─────────────────────────
function renderAlerts(alerts) {
    window._lastAlerts = alerts;
}

// ─── CLOUD SYNC ──────────────────────────────────────────────────────────────
function renderCloudSync(active) {
    const el = document.getElementById('cloud-sync-status');
    if (!el) return;
    if (active) {
        el.innerHTML = '<span class="cloud-icon">&#9729;</span> CLOUD SYNCED';
        el.classList.add('active');
    } else {
        el.innerHTML = '<span class="cloud-icon">&#9729;</span> LOCAL MODE';
        el.classList.remove('active');
    }
}

// ─── STAGE BET ────────────────────────────────────────────────────────────────
async function stageBet() {
    const pick = allPicks.find(p => p.race_no === currentRaceNo);
    if (!pick) return;
    await _doStage(document.getElementById('stage-btn'), pick.horse_no, pick.kelly_stake || 10);
}

async function stageBetHorse(horseNo, stake) {
    await _doStage(event.currentTarget, horseNo, stake);
}

async function _doStage(btn, horseNo, stake) {
    btn.disabled = true;
    btn.textContent = 'STAGING…';
    try {
        const parts  = currentRaceId.split('_');
        const date   = parts[0];
        const venue  = parts[1];
        const resp = await fetch(`${API}/execution/stage_bet`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, venue, race: currentRaceNo, selection: horseNo, stake })
        });
        const result = await resp.json();
        if (result.success) {
            btn.textContent = 'STAGED ✓';
            btn.style.background = '#00c87a';
        } else {
            btn.textContent = 'ERROR';
            btn.style.background = 'var(--red)';
            btn.style.color = '#fff';
        }
    } catch(e) {
        btn.textContent = 'NET ERROR';
        btn.style.background = 'var(--red)';
        btn.style.color = '#fff';
    }
    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = 'STAGE';
        btn.style.background = '';
        btn.style.color = '';
    }, 3000);
}

// ─── COPY BET ────────────────────────────────────────────────────────────────
function copyBet() {
    const pick = allPicks.find(p => p.race_no === currentRaceNo);
    if (!pick) return;
    const line = `${meetingVenue} R${pick.race_no} #${pick.horse_no} ${pick.horse_name || ''} WIN $${pick.kelly_stake || '--'}`;
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(line);
    } else {
        const el = document.createElement('textarea');
        el.value = line; document.body.appendChild(el); el.select();
        document.execCommand('copy'); document.body.removeChild(el);
    }
    const btn = event.currentTarget;
    btn.textContent = 'COPIED ✓';
    setTimeout(() => btn.textContent = '📋 COPY', 2000);
}

// ─── ANALYSIS TOGGLE ─────────────────────────────────────────────────────────
function toggleAnalysis() {
    const toggle = document.getElementById('analysis-toggle');
    const body   = document.getElementById('analysis-body');
    if (!toggle || !body) return;
    toggle.classList.toggle('open');
    body.classList.toggle('open');
}

// ─── HEALTH CHECK ────────────────────────────────────────────────────────────
async function checkHealth() {
    const dot = document.getElementById('health-dot');
    const indicator = document.getElementById('health-indicator');
    if (!dot || !indicator) return;

    try {
        const resp = await fetch(`${API}/health`);
        const data = await resp.json();
        
        if (data.success && data.services?.market_watchdog?.active) {
            const lastHb = data.services.market_watchdog.last_heartbeat;
            const now = new Date();
            const hbDate = lastHb ? new Date(lastHb) : null;
            
            // If heartbeat is older than 5 mins, show warning
            if (hbDate && (now - hbDate) > 300000) {
                dot.className = 'dot warn';
                indicator.title = `Last heartbeat: ${hbDate.toLocaleTimeString()}`;
            } else {
                dot.className = 'dot';
                indicator.title = 'Live Odds Watchdog is active';
            }
        } else {
            dot.className = 'dot err';
            indicator.title = 'Live Odds service offline';
        }
    } catch (e) {
        dot.className = 'dot err';
        indicator.title = 'Cannot reach health API';
    }
}

// ─── BOOTSTRAP ───────────────────────────────────────────────────────────────
poll();
setInterval(poll, POLL_MS);
setInterval(checkHealth, 30000);
checkHealth();
