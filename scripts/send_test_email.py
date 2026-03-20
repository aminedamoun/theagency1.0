"""Send a test email with the full Dubai Prod template."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['EMAIL_USER'] = 'info@dubaiprod.com'
os.environ['EMAIL_PASSWORD'] = 'DubaiProd2025!'
os.environ['EMAIL_SMTP_HOST'] = 'smtp.office365.com'
os.environ['EMAIL_SMTP_PORT'] = '587'

from email_agent.sender import send_email

HOST = 'https://theagency-production.up.railway.app'
O = '#E8900A'
BG = '#1a1a1a'
CARD = '#242424'
TXT = '#b0b0b0'
F = "font-family:'Montserrat',Arial,Helvetica,sans-serif"
NEJC = f'{HOST}/static/img/coo_nejc.jpg'


def divider(label, color=None):
    c = color or O
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td style="height:1px;background:rgba(255,255,255,0.1)"></td>'
        f'<td style="padding:0 16px;white-space:nowrap;font-size:10px;font-weight:700;'
        f'letter-spacing:3px;text-transform:uppercase;color:{c};{F}">{label}</td>'
        f'<td style="height:1px;background:rgba(255,255,255,0.1);width:100%"></td>'
        f'</tr></table>'
    )


def svc_card(name, desc, cta):
    return (
        f'<td width="50%" valign="top" style="padding:6px">'
        f'<div style="background:{CARD};border:1px solid rgba(255,255,255,0.08);'
        f'border-radius:8px;padding:24px 22px;{F}">'
        f'<div style="font-size:18px;font-weight:700;color:{O};margin-bottom:10px">{name}</div>'
        f'<div style="font-size:13px;color:{TXT};line-height:1.7;margin-bottom:16px">{desc}</div>'
        f'<a href="mailto:info@dubaiprod.com" style="display:inline-block;font-size:11px;'
        f'font-weight:600;color:{O};text-decoration:none;border:1px solid rgba(232,144,10,0.3);'
        f'padding:8px 16px;border-radius:20px">{cta}</a>'
        f'</div></td>'
    )


def stat(val, label, border=True):
    bl = f'border-left:1px solid rgba(255,255,255,0.08);' if border else ''
    return (
        f'<td width="25%" style="text-align:center;padding:22px 0;{bl}{F}">'
        f'<div style="font-size:30px;font-weight:800;color:{O}">{val}</div>'
        f'<div style="font-size:9px;font-weight:600;letter-spacing:2px;color:#555;margin-top:6px">{label}</div>'
        f'</td>'
    )


def social_btn(label, url):
    return (
        f'<td style="padding-right:6px"><a href="{url}" style="display:inline-block;'
        f'font-size:10px;font-weight:600;color:{O};text-decoration:none;'
        f'border:1px solid rgba(232,144,10,0.2);padding:5px 12px;border-radius:3px;{F}">'
        f'{label}</a></td>'
    )


html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
*{{margin:0;padding:0}}
body{{background:{BG};{F};color:#fff;margin:0;padding:0}}
table{{border-spacing:0;border-collapse:collapse}}
td{{padding:0}}
img{{border:0;display:block}}
a{{color:{O}}}
</style>
</head>
<body>

<!-- LOGO -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:28px 48px 0;{F};font-size:24px;font-weight:800;letter-spacing:6px;color:#fff">
DUBAI<span style="color:{O}">PROD</span>
</td></tr>
</table>

<!-- HEADER -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:48px 48px 40px">
<h1 style="{F};font-size:46px;font-weight:800;line-height:1.08;color:#fff;margin:0 0 24px">
We Noticed<br><span style="color:{O};font-style:italic;font-weight:700">Room for</span><br>improvement.
</h1>
<table cellpadding="0" cellspacing="0"><tr>
<td style="width:3px;background:{O}"></td>
<td style="padding:12px 0 12px 18px;font-size:14px;color:{TXT};line-height:1.7;{F}">
We noticed a few areas where your digital presence could be strengthened.
</td></tr></table>
</td></tr>
</table>

<!-- MESSAGE -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:16px 48px 36px;font-size:15px;color:{TXT};line-height:1.85;{F}">
Hi Amine,<br><br>
We came across your brand online and noticed a few specific areas where your digital presence could be working harder for you.<br>
This isn't a broadcast — it's a direct observation, and we thought it was worth sharing.
</td></tr>
</table>

<!-- WHAT WE DO -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:36px 48px 8px">{divider('WHAT WE DO FOR YOU')}</td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:12px 42px 28px">
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
{svc_card('Website', 'Modern, professional websites built with image and function in mind — designed to convert visitors into clients.', 'Get Your Website Report →')}
{svc_card('Social Media', 'Strategy, scripting, content production, editing, and publishing — handled end-to-end by our team.', 'Get Social Audit →')}
</tr>
<tr>
{svc_card('Branding', 'Complete elevation of your brand and online optimisation — from visual identity to messaging that resonates.', 'Elevate my Brand →')}
{svc_card('Custom Solutions', "Every project is built on personalisation. Let's find the best digital approach for your business.", "Let's Talk →")}
</tr>
</table>
</td></tr>
</table>

<!-- PORTFOLIO -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:20px 48px 8px">{divider('OUR WORK')}</td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:16px 48px 36px;text-align:center">
<p style="font-size:14px;color:{TXT};line-height:1.7;{F};margin-bottom:20px">
See what we've done for brands across GCC, Europe, and the USA — real projects, real results.
</p>
<a href="https://dubaiprod.com/portfolio" style="display:inline-block;color:{O};font-size:13px;
font-weight:700;letter-spacing:1.5px;text-transform:uppercase;text-decoration:none;
padding:14px 40px;border-radius:4px;border:2px solid {O};{F}">VIEW OUR PORTFOLIO →</a>
</td></tr>
</table>

<!-- TRUST -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:32px 48px 0">{divider('Why Businesses Trust Dubai Prod', '#555')}</td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:24px 48px 0;text-align:center;{F}">
<div style="font-size:36px;font-weight:800;color:#fff">Global Standards.</div>
<div style="font-size:36px;font-weight:800;color:{O};margin-bottom:24px">Local Results.</div>
</td></tr>
</table>
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:0 48px 28px">
<table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.08)">
<tr>
{stat('200+', 'CLIENTS', False)}
{stat('250M+', 'VIEWS')}
{stat('3+', 'CONTINENTS')}
{stat('15+', 'YEARS')}
</tr>
</table>
</td></tr>
</table>

<!-- CTA -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG}">
<tr><td style="padding:40px 48px;text-align:center;{F}">
{divider('READY TO MOVE?')}
<div style="font-size:40px;font-weight:800;color:#fff;line-height:1.15;margin-top:24px">Let's Discuss</div>
<div style="font-size:40px;font-weight:800;color:{O};line-height:1.15;margin-bottom:16px">Your Brand</div>
<p style="font-size:14px;color:{TXT};line-height:1.7;margin:0 auto 28px;max-width:500px">
Reply to this email and we'll share a few tailored ideas for your digital presence — no commitment, no sales pitch, just useful observations.
</p>
<a href="mailto:info@dubaiprod.com" style="display:inline-block;background:{O};color:#fff;
font-size:14px;font-weight:700;letter-spacing:2px;text-transform:uppercase;text-decoration:none;
padding:18px 52px;border-radius:4px">REPLY TO THIS EMAIL</a>
<p style="font-size:12px;color:#555;margin-top:18px">Or reach us directly at info@dubaiprod.com</p>
</td></tr>
</table>

<!-- FOOTER -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#111;border-top:2px solid {O}">
<tr><td style="padding:32px 48px 12px">

<!-- COO Signature Row -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px">
<tr>
<td width="80" valign="top">
<img src="{NEJC}" alt="Nejc Soklic" width="72" height="72"
style="width:72px;height:72px;border-radius:50%;border:2px solid {O}"/>
</td>
<td valign="top" style="padding-left:18px;{F}">
<div style="font-size:18px;font-weight:800;color:#fff;margin-bottom:2px">Nejc Soklic</div>
<div style="font-size:11px;color:{O};font-weight:700;letter-spacing:1px;margin-bottom:8px">COO · DUBAI PROD</div>
<div style="font-size:12px;color:#888;line-height:1.6;font-style:italic">"Global Standards · Local Results"</div>
</td>
</tr>
</table>

<!-- Divider -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px">
<tr><td style="height:1px;background:rgba(255,255,255,0.08)"></td><td style="padding:0 16px;white-space:nowrap;font-size:9px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:{O};{F}">GET IN TOUCH</td><td style="height:1px;background:rgba(255,255,255,0.08);width:100%"></td></tr>
</table>

<!-- Two Columns: Contact + Socials -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td width="50%" valign="top" style="{F}">
<div style="font-size:10px;font-weight:700;color:#555;letter-spacing:2px;margin-bottom:12px">DIRECT CONTACT</div>
<table cellpadding="0" cellspacing="0">
<tr><td style="padding:6px 0;font-size:13px;color:#999">✉&nbsp;&nbsp;<a href="mailto:info@dubaiprod.com" style="color:#ccc;text-decoration:none">info@dubaiprod.com</a></td></tr>
<tr><td style="padding:6px 0;font-size:13px;color:#999">📱&nbsp;&nbsp;+971 54 333 3587 (WhatsApp)</td></tr>
<tr><td style="padding:6px 0;font-size:13px;color:#999">📞&nbsp;&nbsp;+386 40 797 340</td></tr>
<tr><td style="padding:6px 0;font-size:13px;color:#999">🌐&nbsp;&nbsp;<a href="https://dubaiprod.com" style="color:#ccc;text-decoration:none">dubaiprod.com</a></td></tr>
</table>
</td>
<td width="50%" valign="top" style="{F}">
<div style="font-size:10px;font-weight:700;color:#555;letter-spacing:2px;margin-bottom:12px">FOLLOW US</div>
<table cellpadding="0" cellspacing="0" width="100%">
<tr>
<td width="50%" style="padding:4px">
<a href="https://instagram.com/dubaiprod" style="display:block;text-align:center;font-size:11px;font-weight:600;color:{O};text-decoration:none;border:1px solid rgba(232,144,10,0.25);padding:8px 0;border-radius:4px;{F}">📸&nbsp;Instagram</a>
</td>
<td width="50%" style="padding:4px">
<a href="https://linkedin.com/company/dubaiprod" style="display:block;text-align:center;font-size:11px;font-weight:600;color:{O};text-decoration:none;border:1px solid rgba(232,144,10,0.25);padding:8px 0;border-radius:4px;{F}">💼&nbsp;Linkedin</a>
</td>
</tr>
<tr>
<td width="50%" style="padding:4px">
<a href="https://facebook.com/dubaiprod" style="display:block;text-align:center;font-size:11px;font-weight:600;color:{O};text-decoration:none;border:1px solid rgba(232,144,10,0.25);padding:8px 0;border-radius:4px;{F}">📘&nbsp;Facebook</a>
</td>
<td width="50%" style="padding:4px">
<a href="https://youtube.com/@dubaiprod" style="display:block;text-align:center;font-size:11px;font-weight:600;color:{O};text-decoration:none;border:1px solid rgba(232,144,10,0.25);padding:8px 0;border-radius:4px;{F}">▶️&nbsp;Youtube</a>
</td>
</tr>
</table>
</td>
</tr>
</table>

<!-- Copyright -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.06)">
<tr><td style="padding:16px 0 0;text-align:center;font-size:10px;color:#444;{F}">
© 2026 Dubai Prod. All rights reserved. · <a href="#" style="color:#444;text-decoration:underline">Unsubscribe</a>
</td></tr>
</table>

</td></tr>
</table>

</body>
</html>'''

result = send_email(
    to='aminedamoun@gmail.com',
    subject='Dubai Prod — Elevate Your Digital Presence',
    body=html,
    confirm_callback=lambda _: True
)
print('✅ Sent!' if result else '❌ Failed')
