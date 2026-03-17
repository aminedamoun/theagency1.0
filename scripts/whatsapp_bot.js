/**
 * Dubai Prod — WhatsApp Agent Bot
 *
 * 1. Scan QR code once → stays connected
 * 2. Auto-creates "🏢 Dubai Prod Team" group with your number
 * 3. All messages in the group → routed to the AI agents
 * 4. Agents reply in the group with their name + avatar emoji
 *
 * Run: node scripts/whatsapp_bot.js
 */

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode        = require('qrcode-terminal');
const qrcodeImage   = require('qrcode');
const axios         = require('axios');
const path          = require('path');
const fs            = require('fs');
const { execSync }  = require('child_process');

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE    = 'http://localhost:8000';   // FastAPI server
const GROUP_NAME  = 'THE AGENCY 1.0';
const OWNER_PHONE = '971543333587@c.us';       // your WhatsApp ID
const SESSION_DIR = path.join(__dirname, '..', 'config', 'whatsapp_session');

// Agent display names + emoji (shown in group messages)
const AGENTS = {
  sarah:  { name: 'Sarah',  emoji: '👩‍💼', role: 'Manager' },
  marcus: { name: 'Marcus', emoji: '✍️',  role: 'Content' },
  zara:   { name: 'Zara',   emoji: '🎨',  role: 'Designer' },
  kai:    { name: 'Kai',    emoji: '🔍',  role: 'Research' },
  elena:  { name: 'Elena',  emoji: '📊',  role: 'Analytics' },
  alex:   { name: 'Alex',   emoji: '📧',  role: 'Email' },
};

// Keywords that route to specific agents
const ROUTES = {
  sarah:  ['sarah', 'manager', 'task', 'project', 'plan', 'strategy', 'meeting', 'invoice', 'send invoice', 'generate invoice', 'create invoice'],
  marcus: ['marcus', 'content', 'caption', 'copy', 'script', 'hashtag', 'write'],
  zara:   ['zara', 'design', 'image', 'video', 'creative', 'visual', 'voiceover'],
  kai:    ['kai', 'research', 'find', 'search', 'prospect', 'lead', 'company', 'browse'],
  elena:  ['elena', 'analytics', 'report', 'stats', 'performance', 'metric'],
  alex:   ['alex', 'email', 'send email', 'message'],
};

let targetGroupId = null;
let isReady = false;
const botSentIds = new Set(); // track messages sent by the bot to avoid loops

// ── WhatsApp Client ────────────────────────────────────────────────────────────
const client = new Client({
  authStrategy: new LocalAuth({
    clientId: 'dubai-prod-agent',
    dataPath: SESSION_DIR,
  }),
  puppeteer: {
    headless: true,
    protocolTimeout: 180000,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  },
  listenSelfEvents: true,
});

// ── QR Code ───────────────────────────────────────────────────────────────────
client.on('qr', async (qr) => {
  console.log('\n📱 Scan this QR code with your WhatsApp:\n');
  qrcode.generate(qr, { small: true });

  // Also save as image file and open it
  const imgPath = path.join(__dirname, '..', 'whatsapp_qr.png');
  await qrcodeImage.toFile(imgPath, qr, { width: 400, margin: 2 });
  console.log(`\n✅ QR code image saved: ${imgPath}`);
  console.log('📂 Opening QR code image...\n');
  try { execSync(`open "${imgPath}"`); } catch(e) {}
  console.log('Waiting for scan...\n');
});

// ── Ready ─────────────────────────────────────────────────────────────────────
client.on('ready', async () => {
  console.log('✅ WhatsApp connected!\n');
  isReady = true;

  // Start bridge server now that client is ready
  startBridgeServer();

  // Find or create the team group
  await setupGroup();
});

// ── Auth failure ──────────────────────────────────────────────────────────────
client.on('auth_failure', (msg) => {
  console.error('❌ Auth failed:', msg);
});

client.on('disconnected', (reason) => {
  console.log('⚠️  Disconnected:', reason);
  isReady = false;
});

// ── Setup Group ───────────────────────────────────────────────────────────────
async function setupGroup() {
  try {
    const chats = await client.getChats();
    const existing = chats.find(c => c.isGroup && c.name === GROUP_NAME);

    if (existing) {
      targetGroupId = existing.id._serialized;
      console.log(`✅ Group found: "${GROUP_NAME}"`);
      await sendGroupMessage(buildWelcomeMessage());
    } else {
      console.log(`📲 Creating group "${GROUP_NAME}"...`);
      // Create with just owner (can't add fake numbers)
      const group = await client.createGroup(GROUP_NAME, [OWNER_PHONE]);
      targetGroupId = group.gid._serialized;
      console.log(`✅ Group created: "${GROUP_NAME}"`);

      // Send welcome message
      await sendGroupMessage(buildWelcomeMessage());
    }

    console.log(`\n🎯 Listening for messages in "${GROUP_NAME}"...\n`);

  } catch (err) {
    console.error('❌ Group setup error:', err.message);
  }
}

function buildWelcomeMessage() {
  return (
    `🚀 *THE AGENCY 1.0* is online!\n\n` +
    `Your team is ready:\n\n` +
    `👩‍💼 *Sarah* — Manager & Strategy\n` +
    `✍️ *Marcus* — Content & Copywriting\n` +
    `🎨 *Zara* — Design & Creative\n` +
    `🔍 *Kai* — Research & Prospecting\n` +
    `📊 *Elena* — Analytics & Reports\n` +
    `📧 *Alex* — Email & Invoices\n\n` +
    `💬 Type any message — I'll route it to the right agent.\n` +
    `_Example: "Sarah create a content plan for next week"_\n` +
    `_Example: "Kai find 10 restaurants in Dubai"_\n` +
    `_Example: "Alex send invoice to Matyna for 5000 AED"_`
  );
}

// ── Send to Group ─────────────────────────────────────────────────────────────
async function sendGroupMessage(text) {
  if (!targetGroupId) return;
  try {
    const msg = await client.sendMessage(targetGroupId, text);
    if (msg && msg.id && msg.id._serialized) {
      botSentIds.add(msg.id._serialized);
      // Clean up old IDs to avoid memory leak
      if (botSentIds.size > 200) {
        const first = botSentIds.values().next().value;
        botSentIds.delete(first);
      }
    }
  } catch (err) {
    console.error('Send error:', err.message);
  }
}

// ── Route Message to Agent ────────────────────────────────────────────────────
function detectAgent(text) {
  // Sarah handles everything — she is the CEO and delegates internally
  // Only route to specialist if explicitly @mentioned by name
  const lower = text.toLowerCase();
  for (const [key, agent] of Object.entries(AGENTS)) {
    if (key === 'sarah') continue; // Sarah is the default, skip her here
    if (lower.startsWith('@' + agent.name.toLowerCase()) ||
        lower.startsWith(agent.name.toLowerCase() + ' ') ||
        lower.startsWith(agent.name.toLowerCase() + ',')) {
      return key;
    }
  }
  return 'sarah'; // Sarah handles everything by default
}

async function callAgent(agentKey, message) {
  try {
    // Try agent-specific endpoint first
    const res = await axios.post(`${API_BASE}/api/agent-chat`, {
      agent: agentKey,
      message: message,
    }, { timeout: 120000 });
    return res.data.reply || res.data.response || res.data.content || JSON.stringify(res.data);
  } catch (err) {
    // Fallback to general brain
    try {
      const res2 = await axios.post(`${API_BASE}/api/chat`, {
        message: message,
      }, { timeout: 120000 });
      return res2.data.reply || res2.data.response || JSON.stringify(res2.data);
    } catch (err2) {
      return `⚠️ Could not reach the server. Make sure the app is running (python chat.py).`;
    }
  }
}

// ── Message Handler ───────────────────────────────────────────────────────────
async function handleMessage(msg) {
  // Only handle messages from the team group
  // Check both msg.from and msg.id.remote to handle @lid vs @g.us formats
  const chatId = msg.from || (msg.id && msg.id.remote);
  if (!targetGroupId) return;
  if (chatId !== targetGroupId && msg.id && msg.id.remote !== targetGroupId) return;

  // Ignore messages sent by the bot itself (tracked by ID)
  if (botSentIds.has(msg.id._serialized)) return;
  // Also ignore typical bot reply patterns to prevent loops
  if (msg.body && (msg.body.startsWith('👩') || msg.body.startsWith('✍') || msg.body.startsWith('🎨') || msg.body.startsWith('🔍') || msg.body.startsWith('📊') || msg.body.startsWith('📧') || msg.body.startsWith('🏢') || msg.body.startsWith('🔔'))) return;

  const text = msg.body.trim();
  if (!text || text.length < 2) return;

  console.log(`💬 Group message: "${text.substring(0, 60)}..."`);

  // Typing indicator
  const chat = await msg.getChat();
  await chat.sendStateTyping();

  // Route to correct agent
  const agentKey = detectAgent(text);
  const agent    = AGENTS[agentKey];

  // Send "agent is working" notice
  await sendGroupMessage(`${agent.emoji} *${agent.name}* is on it...`);

  try {
    const reply = await callAgent(agentKey, text);

    // Format reply with agent signature
    const formatted =
      `${agent.emoji} *${agent.name}* _(${agent.role})_\n` +
      `${'─'.repeat(30)}\n` +
      reply.substring(0, 3500) +  // WhatsApp message limit ~4000 chars
      (reply.length > 3500 ? '\n\n_[message truncated — see the app for full response]_' : '');

    await sendGroupMessage(formatted);
    console.log(`✅ ${agent.name} replied (${reply.length} chars)`);

  } catch (err) {
    await sendGroupMessage(`❌ *Error:* ${err.message}`);
    console.error('Agent error:', err.message);
  }

  await chat.clearState();
}

// Listen on BOTH events — 'message' for incoming, 'message_create' catches your own messages too
client.on('message', (msg) => {
  console.log(`[DEBUG] message event: from=${msg.from} targetGroup=${targetGroupId} fromMe=${msg.fromMe} body=${msg.body ? msg.body.substring(0,30) : ''}`);
  handleMessage(msg);
});
client.on('message_create', (msg) => {
  console.log(`[DEBUG] message_create event: from=${msg.from} targetGroup=${targetGroupId} fromMe=${msg.fromMe} body=${msg.body ? msg.body.substring(0,30) : ''}`);
  handleMessage(msg);
});

// ── HTTP bridge server (started once WhatsApp is ready) ──────────────────────
const http = require('http');
function startBridgeServer() {
  const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/send') {
      let body = '';
      req.on('data', d => body += d);
      req.on('end', async () => {
        try {
          const { message, phone } = JSON.parse(body);
          if (phone) {
            const wid = phone.replace(/\D/g, '') + '@c.us';
            await client.sendMessage(wid, message);
          } else if (targetGroupId) {
            await sendGroupMessage(message);
          }
          res.writeHead(200); res.end(JSON.stringify({ ok: true }));
        } catch (e) {
          res.writeHead(500); res.end(JSON.stringify({ error: e.message }));
        }
      });
    } else {
      res.writeHead(404); res.end();
    }
  });
  server.on('error', (e) => {
    if (e.code === 'EADDRINUSE') {
      console.log('⚠️  Port 3001 in use — bridge already running, skipping.');
    } else {
      console.error('Bridge server error:', e.message);
    }
  });
  server.listen(3001, () => console.log('📡 WhatsApp bridge running on port 3001'));
}

// ── Start ─────────────────────────────────────────────────────────────────────
console.log('\n🚀 Starting Dubai Prod WhatsApp Bot...');
console.log('📱 A QR code will appear — scan it with WhatsApp on your phone.\n');
client.initialize();
