// ══════════ CREATIVE STUDIO TEMPLATE LIBRARY ══════════
// Each template: { name, category, format, bg (color/gradient/image URL), elements[] }
// Elements: { type:'text'|'rect'|'circle', text, x(%), y(%), size, weight, color, font, ... }

const TEMPLATE_CATEGORIES = [
  { id:'all', label:'All', icon:'🎨' },
  { id:'post', label:'Instagram Post', icon:'📸' },
  { id:'story', label:'Story / Reel', icon:'📱' },
  { id:'youtube', label:'YouTube Thumbnail', icon:'📺' },
  { id:'fitness', label:'Fitness & Gym', icon:'💪' },
  { id:'food', label:'Food & Restaurant', icon:'🍽' },
  { id:'realestate', label:'Real Estate', icon:'🏠' },
  { id:'fashion', label:'Fashion & Beauty', icon:'👗' },
  { id:'business', label:'Business & Corporate', icon:'💼' },
  { id:'event', label:'Events & Party', icon:'🎉' },
  { id:'travel', label:'Travel & Lifestyle', icon:'✈️' },
  { id:'quote', label:'Quotes & Motivation', icon:'💬' },
  { id:'sale', label:'Sales & Promo', icon:'🏷️' },
  { id:'minimal', label:'Minimal & Clean', icon:'✨' },
];

const TEMPLATE_LIBRARY = [
  // ── INSTAGRAM POST (1024x1024) ──
  { name:'Dark Luxury Gold', category:['post','business','minimal'], format:'1024x1024',
    bg:'linear-gradient(160deg,#0a0a0a,#1a1a2e)',
    elements:[
      {type:'rect',x:5,y:5,w:90,h:90,fill:'transparent',stroke:'#c9a84c',strokeWidth:1},
      {type:'text',text:'PREMIUM',x:50,y:35,size:48,weight:900,color:'#c9a84c',font:'Georgia'},
      {type:'text',text:'COLLECTION',x:50,y:48,size:20,weight:300,color:'#fff',font:'Georgia',spacing:600},
      {type:'rect',x:35,y:58,w:30,h:0.5,fill:'#c9a84c'},
      {type:'text',text:'2026 Edition',x:50,y:65,size:14,weight:400,color:'rgba(255,255,255,0.5)',font:'Georgia'},
    ]},
  { name:'Bold Red Energy', category:['post','fitness','sale'], format:'1024x1024',
    bg:'linear-gradient(135deg,#1a1a1a,#2d0a0a)',
    elements:[
      {type:'text',text:'50% OFF',x:50,y:30,size:56,weight:900,color:'#e74c3c',font:'Impact'},
      {type:'text',text:'LIMITED TIME OFFER',x:50,y:45,size:16,weight:700,color:'#fff',font:'Arial',spacing:400},
      {type:'rect',x:25,y:55,w:50,h:0.5,fill:'#e74c3c'},
      {type:'text',text:'SHOP NOW →',x:50,y:65,size:18,weight:700,color:'#e74c3c',font:'Arial'},
    ]},
  { name:'Ocean Blue Fresh', category:['post','travel','business'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0c2340,#1a5276)',
    elements:[
      {type:'circle',x:50,y:35,r:15,fill:'rgba(52,152,219,0.2)',stroke:'rgba(52,152,219,0.4)'},
      {type:'text',text:'DISCOVER',x:50,y:32,size:36,weight:900,color:'#fff',font:'Segoe UI'},
      {type:'text',text:'New Horizons',x:50,y:45,size:20,weight:300,color:'rgba(255,255,255,0.7)',font:'Georgia'},
      {type:'text',text:'LEARN MORE',x:50,y:75,size:12,weight:700,color:'#3498db',font:'Arial',spacing:300},
    ]},
  { name:'Neon Purple', category:['post','event','fashion'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0a0015,#1a0a30)',
    elements:[
      {type:'text',text:'TONIGHT',x:50,y:35,size:52,weight:900,color:'#9b59b6',font:'Impact',shadow:'0 0 20px rgba(155,89,182,0.8)'},
      {type:'text',text:'THE BIGGEST EVENT OF THE YEAR',x:50,y:50,size:14,weight:400,color:'rgba(255,255,255,0.6)',font:'Arial'},
      {type:'rect',x:30,y:58,w:40,h:8,fill:'#9b59b6',radius:4},
      {type:'text',text:'GET TICKETS',x:50,y:60,size:14,weight:700,color:'#fff',font:'Arial'},
    ]},
  { name:'Warm Sunset', category:['post','travel','food'], format:'1024x1024',
    bg:'linear-gradient(135deg,#f39c12,#e74c3c)',
    elements:[
      {type:'text',text:'Summer',x:50,y:35,size:48,weight:300,color:'#fff',font:'Georgia'},
      {type:'text',text:'VIBES',x:50,y:50,size:36,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'☀',x:50,y:18,size:32,weight:400,color:'rgba(255,255,255,0.8)'},
    ]},
  { name:'Clean White Minimal', category:['post','minimal','business'], format:'1024x1024',
    bg:'#ffffff',
    elements:[
      {type:'text',text:'Less is',x:50,y:38,size:36,weight:300,color:'#333',font:'Georgia'},
      {type:'text',text:'MORE',x:50,y:52,size:48,weight:900,color:'#000',font:'Georgia'},
      {type:'rect',x:42,y:62,w:16,h:0.5,fill:'#000'},
    ]},
  { name:'Green Nature', category:['post','travel','food'], format:'1024x1024',
    bg:'linear-gradient(160deg,#0a1f0a,#1a3a1a)',
    elements:[
      {type:'text',text:'🌿',x:50,y:20,size:40,weight:400,color:'#fff'},
      {type:'text',text:'ORGANIC',x:50,y:38,size:40,weight:900,color:'#2ecc71',font:'Georgia'},
      {type:'text',text:'& NATURAL',x:50,y:50,size:18,weight:300,color:'rgba(255,255,255,0.6)',font:'Georgia',spacing:500},
      {type:'text',text:'Farm to Table',x:50,y:65,size:16,weight:400,color:'#2ecc71',font:'Georgia'},
    ]},
  { name:'Pink Feminine', category:['post','fashion','event'], format:'1024x1024',
    bg:'linear-gradient(135deg,#fce4ec,#f8bbd0)',
    elements:[
      {type:'text',text:'NEW',x:50,y:30,size:14,weight:700,color:'#c2185b',font:'Arial',spacing:600},
      {type:'text',text:'Spring',x:50,y:42,size:48,weight:300,color:'#880e4f',font:'Georgia'},
      {type:'text',text:'COLLECTION',x:50,y:55,size:20,weight:700,color:'#c2185b',font:'Arial',spacing:300},
      {type:'text',text:'shop now',x:50,y:72,size:14,weight:400,color:'#880e4f',font:'Georgia'},
    ]},

  // ── FITNESS ──
  { name:'Gym Dark Power', category:['post','fitness'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0a0a0a,#1a0a0a)',
    elements:[
      {type:'text',text:'NO',x:50,y:25,size:60,weight:900,color:'#e74c3c',font:'Impact'},
      {type:'text',text:'EXCUSES',x:50,y:42,size:52,weight:900,color:'#fff',font:'Impact'},
      {type:'rect',x:20,y:55,w:60,h:0.5,fill:'#e74c3c'},
      {type:'text',text:'PERSONAL TRAINING',x:50,y:62,size:14,weight:600,color:'rgba(255,255,255,0.5)',font:'Arial',spacing:400},
      {type:'text',text:'START TODAY',x:50,y:80,size:16,weight:700,color:'#e74c3c',font:'Arial'},
    ]},
  { name:'Fitness Promo', category:['post','fitness','sale'], format:'1024x1024',
    bg:'linear-gradient(135deg,#1a1a2e,#16213e)',
    elements:[
      {type:'text',text:'30% OFF',x:50,y:25,size:52,weight:900,color:'#c9a84c',font:'Impact'},
      {type:'text',text:'PERSONAL TRAINING',x:50,y:40,size:20,weight:700,color:'#fff',font:'Arial'},
      {type:'text',text:'Transform your body in 12 weeks',x:50,y:52,size:14,weight:400,color:'rgba(255,255,255,0.6)',font:'Arial'},
      {type:'rect',x:30,y:65,w:40,h:8,fill:'#c9a84c',radius:4},
      {type:'text',text:'BOOK NOW',x:50,y:67,size:14,weight:700,color:'#000',font:'Arial'},
    ]},

  // ── FOOD & RESTAURANT ──
  { name:'Restaurant Dark Elegant', category:['post','food'], format:'1024x1024',
    bg:'linear-gradient(160deg,#0a0a0a,#1a0f05)',
    elements:[
      {type:'text',text:'🍽',x:50,y:18,size:30,weight:400,color:'#fff'},
      {type:'text',text:'FINE DINING',x:50,y:32,size:14,weight:600,color:'#c9a84c',font:'Arial',spacing:600},
      {type:'text',text:'Chef\'s Special',x:50,y:42,size:36,weight:300,color:'#fff',font:'Georgia'},
      {type:'rect',x:35,y:52,w:30,h:0.3,fill:'#c9a84c'},
      {type:'text',text:'Reserve Your Table',x:50,y:60,size:14,weight:400,color:'rgba(255,255,255,0.5)',font:'Georgia'},
    ]},
  { name:'Pizza Night', category:['post','food','event'], format:'1024x1024',
    bg:'linear-gradient(135deg,#2d0a0a,#1a0a00)',
    elements:[
      {type:'text',text:'🍕',x:50,y:18,size:40,weight:400,color:'#fff'},
      {type:'text',text:'PIZZA',x:50,y:35,size:56,weight:900,color:'#f39c12',font:'Impact'},
      {type:'text',text:'NIGHT',x:50,y:50,size:36,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'Every Friday 7PM',x:50,y:65,size:14,weight:400,color:'rgba(255,255,255,0.5)',font:'Arial'},
    ]},

  // ── REAL ESTATE ──
  { name:'Luxury Property', category:['post','realestate'], format:'1024x1024',
    bg:'linear-gradient(160deg,#0a0a15,#1a1a30)',
    elements:[
      {type:'rect',x:5,y:5,w:90,h:90,fill:'transparent',stroke:'#c9a84c',strokeWidth:0.5},
      {type:'text',text:'FOR SALE',x:50,y:20,size:12,weight:700,color:'#c9a84c',font:'Arial',spacing:600},
      {type:'text',text:'LUXURY',x:50,y:35,size:48,weight:900,color:'#fff',font:'Georgia'},
      {type:'text',text:'PENTHOUSE',x:50,y:48,size:24,weight:300,color:'rgba(255,255,255,0.7)',font:'Georgia',spacing:400},
      {type:'text',text:'AED 5,500,000',x:50,y:62,size:20,weight:700,color:'#c9a84c',font:'Arial'},
      {type:'text',text:'4 Beds • 5 Baths • 4,200 sqft',x:50,y:72,size:12,weight:400,color:'rgba(255,255,255,0.4)',font:'Arial'},
    ]},
  { name:'Property Modern', category:['post','realestate','minimal'], format:'1024x1024',
    bg:'#f5f5f5',
    elements:[
      {type:'text',text:'NEW LISTING',x:50,y:15,size:10,weight:700,color:'#e74c3c',font:'Arial',spacing:500},
      {type:'text',text:'Palm Jumeirah',x:50,y:30,size:36,weight:300,color:'#1a1a2e',font:'Georgia'},
      {type:'text',text:'VILLA',x:50,y:42,size:28,weight:900,color:'#1a1a2e',font:'Georgia'},
      {type:'rect',x:40,y:50,w:20,h:0.3,fill:'#c9a84c'},
      {type:'text',text:'Starting from AED 8.2M',x:50,y:58,size:14,weight:600,color:'#c9a84c',font:'Arial'},
    ]},

  // ── STORIES (1024x1792) ──
  { name:'Story Dark Promo', category:['story','sale'], format:'1024x1792',
    bg:'linear-gradient(180deg,#0a0a15,#1a0a20,#0a0a15)',
    elements:[
      {type:'text',text:'SWIPE UP',x:50,y:90,size:12,weight:700,color:'#c9a84c',font:'Arial',spacing:400},
      {type:'text',text:'BIG',x:50,y:30,size:64,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'SALE',x:50,y:42,size:64,weight:900,color:'#e74c3c',font:'Impact'},
      {type:'text',text:'Up to 70% OFF',x:50,y:55,size:20,weight:400,color:'rgba(255,255,255,0.6)',font:'Arial'},
    ]},
  { name:'Story Gradient Quote', category:['story','quote'], format:'1024x1792',
    bg:'linear-gradient(180deg,#667eea,#764ba2)',
    elements:[
      {type:'text',text:'"',x:50,y:25,size:80,weight:300,color:'rgba(255,255,255,0.3)',font:'Georgia'},
      {type:'text',text:'The only way to do\ngreat work is to love\nwhat you do.',x:50,y:40,size:24,weight:400,color:'#fff',font:'Georgia'},
      {type:'text',text:'— Steve Jobs',x:50,y:62,size:14,weight:600,color:'rgba(255,255,255,0.7)',font:'Arial'},
    ]},
  { name:'Story Fitness CTA', category:['story','fitness'], format:'1024x1792',
    bg:'linear-gradient(180deg,#0a0a0a,#1a0a0a)',
    elements:[
      {type:'text',text:'💪',x:50,y:20,size:48,weight:400,color:'#fff'},
      {type:'text',text:'YOUR JOURNEY',x:50,y:35,size:28,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'STARTS NOW',x:50,y:42,size:28,weight:900,color:'#e74c3c',font:'Impact'},
      {type:'text',text:'Free trial class\navailable this week',x:50,y:55,size:16,weight:400,color:'rgba(255,255,255,0.5)',font:'Arial'},
      {type:'rect',x:25,y:70,w:50,h:7,fill:'#e74c3c',radius:20},
      {type:'text',text:'SIGN UP NOW',x:50,y:72,size:14,weight:700,color:'#fff',font:'Arial'},
    ]},
  { name:'Story Food Special', category:['story','food'], format:'1024x1792',
    bg:'linear-gradient(180deg,#1a0f05,#0a0500)',
    elements:[
      {type:'text',text:'TODAY\'S',x:50,y:25,size:16,weight:600,color:'#c9a84c',font:'Arial',spacing:500},
      {type:'text',text:'SPECIAL',x:50,y:33,size:48,weight:900,color:'#fff',font:'Georgia'},
      {type:'rect',x:30,y:42,w:40,h:0.3,fill:'#c9a84c'},
      {type:'text',text:'Wagyu Beef Burger\nwith Truffle Fries',x:50,y:50,size:18,weight:400,color:'rgba(255,255,255,0.7)',font:'Georgia'},
      {type:'text',text:'AED 89',x:50,y:65,size:28,weight:700,color:'#c9a84c',font:'Arial'},
      {type:'text',text:'ORDER NOW ↑',x:50,y:88,size:12,weight:700,color:'#c9a84c',font:'Arial',spacing:300},
    ]},
  { name:'Story Real Estate', category:['story','realestate'], format:'1024x1792',
    bg:'linear-gradient(180deg,#0a1520,#0a0a15)',
    elements:[
      {type:'text',text:'JUST LISTED',x:50,y:15,size:12,weight:700,color:'#c9a84c',font:'Arial',spacing:500},
      {type:'text',text:'Downtown',x:50,y:30,size:36,weight:300,color:'#fff',font:'Georgia'},
      {type:'text',text:'DUBAI',x:50,y:38,size:36,weight:900,color:'#fff',font:'Georgia'},
      {type:'text',text:'2 BR Apartment\nBurj Khalifa View',x:50,y:52,size:16,weight:400,color:'rgba(255,255,255,0.5)',font:'Arial'},
      {type:'text',text:'AED 2,800,000',x:50,y:65,size:24,weight:700,color:'#c9a84c',font:'Arial'},
      {type:'text',text:'DM for Details ↑',x:50,y:88,size:12,weight:600,color:'rgba(255,255,255,0.4)',font:'Arial'},
    ]},

  // ── YOUTUBE THUMBNAILS (1792x1024) ──
  { name:'YouTube Bold', category:['youtube'], format:'1792x1024',
    bg:'linear-gradient(135deg,#e74c3c,#c0392b)',
    elements:[
      {type:'text',text:'YOU WON\'T',x:50,y:30,size:48,weight:900,color:'#fff',font:'Impact',shadow:'0 4px 8px rgba(0,0,0,0.5)'},
      {type:'text',text:'BELIEVE THIS!',x:50,y:50,size:52,weight:900,color:'#ff0',font:'Impact',shadow:'0 4px 8px rgba(0,0,0,0.5)'},
    ]},
  { name:'YouTube Tutorial', category:['youtube','business'], format:'1792x1024',
    bg:'linear-gradient(135deg,#1a1a2e,#2d2d4f)',
    elements:[
      {type:'rect',x:3,y:15,w:45,h:70,fill:'rgba(155,89,182,0.15)',radius:8},
      {type:'text',text:'HOW TO',x:28,y:30,size:20,weight:700,color:'#9b59b6',font:'Arial'},
      {type:'text',text:'Make Money\nOnline in 2026',x:28,y:45,size:32,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'Step by Step Guide',x:28,y:70,size:14,weight:400,color:'rgba(255,255,255,0.5)',font:'Arial'},
    ]},
  { name:'YouTube Fitness', category:['youtube','fitness'], format:'1792x1024',
    bg:'linear-gradient(135deg,#0a0a0a,#1a0505)',
    elements:[
      {type:'text',text:'30 DAY',x:30,y:30,size:44,weight:900,color:'#e74c3c',font:'Impact'},
      {type:'text',text:'TRANSFORMATION',x:30,y:48,size:36,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'CHALLENGE',x:30,y:62,size:28,weight:900,color:'#f39c12',font:'Impact'},
    ]},

  // ── QUOTES ──
  { name:'Motivational Dark', category:['post','quote'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0a0a0a,#1a1a1a)',
    elements:[
      {type:'text',text:'"',x:15,y:20,size:80,weight:300,color:'rgba(201,168,76,0.3)',font:'Georgia'},
      {type:'text',text:'Success is not final,\nfailure is not fatal.',x:50,y:40,size:24,weight:400,color:'#fff',font:'Georgia'},
      {type:'rect',x:15,y:60,w:20,h:0.5,fill:'#c9a84c'},
      {type:'text',text:'Winston Churchill',x:25,y:67,size:12,weight:600,color:'#c9a84c',font:'Arial'},
    ]},
  { name:'Quote Gradient', category:['post','quote','story'], format:'1024x1024',
    bg:'linear-gradient(135deg,#4facfe,#00f2fe)',
    elements:[
      {type:'text',text:'DREAM\nBIG',x:50,y:35,size:52,weight:900,color:'#fff',font:'Impact',shadow:'0 4px 12px rgba(0,0,0,0.3)'},
      {type:'text',text:'Work hard. Stay humble.',x:50,y:62,size:16,weight:400,color:'rgba(255,255,255,0.8)',font:'Georgia'},
    ]},

  // ── EVENTS ──
  { name:'Event Party Neon', category:['post','event'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0a0015,#150025)',
    elements:[
      {type:'text',text:'FRIDAY',x:50,y:20,size:14,weight:700,color:'#e91e63',font:'Arial',spacing:600},
      {type:'text',text:'NIGHT',x:50,y:32,size:52,weight:900,color:'#fff',font:'Impact',shadow:'0 0 30px rgba(233,30,99,0.5)'},
      {type:'text',text:'PARTY',x:50,y:48,size:52,weight:900,color:'#e91e63',font:'Impact',shadow:'0 0 30px rgba(233,30,99,0.5)'},
      {type:'text',text:'DJ MARCO • 10PM • FREE ENTRY',x:50,y:65,size:12,weight:600,color:'rgba(255,255,255,0.5)',font:'Arial',spacing:200},
    ]},

  // ── FASHION ──
  { name:'Fashion Minimal', category:['post','fashion','minimal'], format:'1024x1024',
    bg:'#f0ebe3',
    elements:[
      {type:'text',text:'NEW IN',x:50,y:25,size:10,weight:700,color:'#8d6e63',font:'Arial',spacing:600},
      {type:'text',text:'Autumn',x:50,y:38,size:44,weight:300,color:'#3e2723',font:'Georgia'},
      {type:'text',text:'ESSENTIALS',x:50,y:52,size:18,weight:700,color:'#3e2723',font:'Arial',spacing:400},
      {type:'rect',x:42,y:60,w:16,h:0.3,fill:'#8d6e63'},
    ]},
  { name:'Fashion Dark', category:['post','fashion'], format:'1024x1024',
    bg:'#0a0a0a',
    elements:[
      {type:'text',text:'VOGUE',x:50,y:20,size:14,weight:400,color:'rgba(255,255,255,0.3)',font:'Georgia',spacing:800},
      {type:'text',text:'STYLE',x:50,y:38,size:56,weight:100,color:'#fff',font:'Georgia',spacing:600},
      {type:'rect',x:35,y:50,w:30,h:0.3,fill:'rgba(255,255,255,0.3)'},
      {type:'text',text:'SS26',x:50,y:58,size:18,weight:700,color:'rgba(255,255,255,0.5)',font:'Arial',spacing:400},
    ]},

  // ── BUSINESS ──
  { name:'Corporate Blue', category:['post','business'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0c2340,#1565c0)',
    elements:[
      {type:'text',text:'ANNUAL',x:50,y:30,size:16,weight:600,color:'rgba(255,255,255,0.5)',font:'Arial',spacing:500},
      {type:'text',text:'REPORT',x:50,y:42,size:44,weight:900,color:'#fff',font:'Arial'},
      {type:'text',text:'2026',x:50,y:56,size:28,weight:300,color:'rgba(255,255,255,0.5)',font:'Arial'},
      {type:'rect',x:35,y:65,w:30,h:0.3,fill:'rgba(255,255,255,0.3)'},
    ]},
  { name:'Webinar Promo', category:['post','business','event'], format:'1024x1024',
    bg:'linear-gradient(135deg,#1a1a2e,#2d2d4f)',
    elements:[
      {type:'text',text:'FREE WEBINAR',x:50,y:18,size:12,weight:700,color:'#3498db',font:'Arial',spacing:500},
      {type:'text',text:'Digital Marketing\nMasterclass',x:50,y:35,size:28,weight:700,color:'#fff',font:'Segoe UI'},
      {type:'text',text:'Learn how to grow your business\nonline with proven strategies',x:50,y:55,size:12,weight:400,color:'rgba(255,255,255,0.5)',font:'Arial'},
      {type:'rect',x:25,y:70,w:50,h:8,fill:'#3498db',radius:4},
      {type:'text',text:'REGISTER FREE',x:50,y:72,size:14,weight:700,color:'#fff',font:'Arial'},
    ]},

  // ── TRAVEL ──
  { name:'Travel Adventure', category:['post','travel'], format:'1024x1024',
    bg:'linear-gradient(135deg,#0f4c75,#3282b8)',
    elements:[
      {type:'text',text:'✈',x:50,y:18,size:36,weight:400,color:'rgba(255,255,255,0.5)'},
      {type:'text',text:'WANDERLUST',x:50,y:35,size:36,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'Explore the world',x:50,y:48,size:18,weight:300,color:'rgba(255,255,255,0.7)',font:'Georgia'},
      {type:'text',text:'Book your next adventure',x:50,y:70,size:12,weight:400,color:'rgba(255,255,255,0.4)',font:'Arial'},
    ]},

  // ── SALE / PROMO ──
  { name:'Flash Sale Red', category:['post','sale'], format:'1024x1024',
    bg:'linear-gradient(135deg,#b71c1c,#e53935)',
    elements:[
      {type:'text',text:'⚡ FLASH SALE',x:50,y:25,size:16,weight:700,color:'#ff0',font:'Arial',spacing:300},
      {type:'text',text:'70%',x:50,y:42,size:72,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'OFF EVERYTHING',x:50,y:58,size:18,weight:700,color:'#fff',font:'Arial'},
      {type:'text',text:'Today Only • Code: FLASH70',x:50,y:72,size:12,weight:400,color:'rgba(255,255,255,0.7)',font:'Arial'},
    ]},
  { name:'Black Friday', category:['post','sale','event'], format:'1024x1024',
    bg:'#000',
    elements:[
      {type:'text',text:'BLACK',x:50,y:30,size:52,weight:900,color:'#fff',font:'Impact'},
      {type:'text',text:'FRIDAY',x:50,y:48,size:52,weight:900,color:'#c9a84c',font:'Impact'},
      {type:'text',text:'Up to 80% off on everything',x:50,y:62,size:14,weight:400,color:'rgba(255,255,255,0.4)',font:'Arial'},
      {type:'rect',x:30,y:72,w:40,h:7,fill:'#c9a84c',radius:4},
      {type:'text',text:'SHOP NOW',x:50,y:74,size:14,weight:700,color:'#000',font:'Arial'},
    ]},
];
