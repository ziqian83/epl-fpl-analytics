import { mkdir, writeFile } from 'node:fs/promises';

const API = 'https://fantasy.premierleague.com/api';
const OUT = new URL('../boot-room/picker/data/player-signals.json', import.meta.url);
const bootstrap = await fetch(`${API}/bootstrap-static/`).then(check).then(r => r.json());
const players = bootstrap.elements;
const signals = {};
let cursor = 0;

async function worker() {
  while (cursor < players.length) {
    const player = players[cursor++];
    try {
      const data = await fetch(`${API}/element-summary/${player.id}/`).then(check).then(r => r.json());
      const recent = data.history.slice(-6);
      const full = recent.filter(row => row.minutes >= 60);
      signals[player.code] = {
        consistency: full.length ? full.filter(row => row.total_points >= 4).length / full.length : 0,
        xgi: recent.reduce((sum, row) => sum + Number(row.expected_goal_involvements || 0), 0),
        starts: full.length
      };
    } catch (error) {
      console.warn(`Skipped ${player.web_name} (${player.code}): ${error.message}`);
    }
  }
}

function check(response) {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response;
}

await Promise.all(Array.from({ length: 16 }, worker));
await mkdir(new URL('../boot-room/picker/data/', import.meta.url), { recursive: true });
await writeFile(OUT, `${JSON.stringify({
  generated_at: new Date().toISOString(),
  source: `${API}/element-summary/{element_id}/`,
  window: 'last 6 gameweeks; consistency uses 60+ minute matches',
  players: signals
}, null, 2)}\n`);
console.log(`Wrote ${Object.keys(signals).length}/${players.length} player histories to ${OUT.pathname}`);
const current = bootstrap.events.find(event => event.is_current) || bootstrap.events.filter(event => event.finished).at(-1);
const next = bootstrap.events.find(event => event.is_next) || bootstrap.events.find(event => !event.finished);
const [entry, picks, fixtures] = await Promise.all([
  fetch(`${API}/entry/4120529/`).then(check).then(r => r.json()),
  fetch(`${API}/entry/4120529/event/${current.id}/picks/`).then(check).then(r => r.json()),
  fetch(`${API}/fixtures/?event=${next.id}`).then(check).then(r => r.json())
]);
await writeFile(new URL('../boot-room/picker/data/live-state.json', import.meta.url), `${JSON.stringify({generated_at:new Date().toISOString(),bootstrap,entry,picks,fixtures},null,2)}\n`);
