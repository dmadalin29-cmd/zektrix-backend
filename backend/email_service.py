# -*- coding: utf-8 -*-
"""Email service for Zektrix UK Competition Platform"""
import os
import asyncio
import logging
import resend

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@zektrix.uk')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


async def send_winner_notification_email(winner_email: str, winner_name: str, competition_title: str, prize_description: str, ticket_number: int):
    if not RESEND_API_KEY:
        return None
    html_content = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;max-width:600px;margin:0 auto;background:#030014;color:white;padding:0;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#8b5cf6,#d946ef);padding:30px;text-align:center;">
            <h1 style="margin:0;font-size:32px;font-weight:900;">FELICITARI!</h1>
            <p style="margin:8px 0 0 0;font-size:16px;opacity:0.9;">Ai castigat la Zektrix UK!</p>
        </div>
        <div style="padding:30px;">
            <p style="color:#9ca3af;font-size:15px;">Draga <strong style="color:#fff;">{winner_name}</strong>,</p>
            <p style="color:#9ca3af;font-size:14px;line-height:1.6;">Suntem incantati sa te anuntam ca esti castigatorul competitiei:</p>
            <div style="background:#0d0b1a;border:1px solid #8b5cf630;border-radius:12px;padding:20px;margin:20px 0;text-align:center;">
                <h3 style="color:#fbbf24;font-size:20px;margin:0 0 8px 0;">{competition_title}</h3>
                <p style="color:#9ca3af;margin:4px 0;font-size:13px;">Premiu: <strong style="color:#10b981;">{prize_description or 'Vezi detalii pe site'}</strong></p>
                <p style="color:#9ca3af;margin:4px 0;font-size:13px;">Loc castigator: <strong style="color:#fbbf24;">#{ticket_number}</strong></p>
            </div>
            <div style="background:#0d0b1a;border:1px solid #1e1b3a;border-radius:12px;padding:20px;margin:20px 0;">
                <h4 style="color:#8b5cf6;margin:0 0 12px 0;font-size:14px;">Urmatorii pasi:</h4>
                <p style="color:#9ca3af;margin:0 0 8px 0;font-size:13px;">1. Te vom contacta in 24-48 ore cu instructiuni</p>
                <p style="color:#9ca3af;margin:0 0 8px 0;font-size:13px;">2. Pregateste documentele de identitate</p>
                <p style="color:#9ca3af;margin:0;font-size:13px;">3. Verifica folderul spam</p>
            </div>
            <div style="text-align:center;padding:10px 0 20px 0;">
                <a href="https://zektrix.uk/dashboard" style="display:inline-block;background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#fff;text-decoration:none;padding:14px 40px;border-radius:50px;font-weight:700;font-size:14px;">CONTUL MEU</a>
            </div>
            <div style="text-align:center;border-top:1px solid #1e1b3a;padding-top:16px;">
                <p style="color:#4b5563;font-size:10px;margin:0;">&#169; 2026 Zektrix UK Ltd &bull; <a href="https://zektrix.uk" style="color:#8b5cf6;text-decoration:none;">zektrix.uk</a></p>
            </div>
        </div>
    </div>"""
    try:
        email = await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL, "to": [winner_email],
            "subject": f"[CASTIGATOR] Felicitari! Ai castigat la {competition_title}!",
            "html": html_content
        })
        logger.info(f"Winner notification email sent to {winner_email}")
        return email.get("id")
    except Exception as e:
        logger.error(f"Failed to send winner email: {str(e)}")
        return None


async def send_welcome_email(user_email: str, username: str, referral_code: str):
    if not RESEND_API_KEY:
        return None
    html_content = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;max-width:600px;margin:0 auto;background:#030014;color:white;padding:0;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#8b5cf6,#7c3aed);padding:30px;text-align:center;">
            <h1 style="margin:0;font-size:28px;font-weight:900;"><span style="color:#fff;">ZEKTRIX</span>.UK</h1>
            <p style="margin:8px 0 0 0;font-size:15px;opacity:0.9;">Bine ai venit!</p>
        </div>
        <div style="padding:30px;">
            <p style="color:#9ca3af;font-size:15px;">Salut <strong style="color:#fff;">{username}</strong>,</p>
            <p style="color:#9ca3af;font-size:14px;line-height:1.6;">Iti multumim ca te-ai alaturat platformei noastre de competitii!</p>
            <div style="background:#0d0b1a;border:1px solid #8b5cf630;border-radius:12px;padding:20px;margin:20px 0;text-align:center;">
                <p style="color:#8b5cf6;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px 0;">Codul tau de referral</p>
                <p style="font-size:24px;margin:0;font-weight:800;color:#fbbf24;letter-spacing:3px;font-family:monospace;">{referral_code}</p>
                <p style="color:#6b7280;font-size:12px;margin:8px 0 0 0;">Invita prieteni si castigi £5 pentru fiecare!</p>
            </div>
            <div style="text-align:center;padding:10px 0 20px 0;">
                <a href="https://zektrix.uk/competitions" style="display:inline-block;background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#fff;text-decoration:none;padding:14px 40px;border-radius:50px;font-weight:700;font-size:14px;">VEZI COMPETITIILE</a>
            </div>
            <div style="text-align:center;border-top:1px solid #1e1b3a;padding-top:16px;">
                <p style="color:#4b5563;font-size:10px;margin:0;">&#169; 2026 Zektrix UK Ltd &bull; <a href="https://zektrix.uk" style="color:#8b5cf6;text-decoration:none;">zektrix.uk</a></p>
            </div>
        </div>
    </div>"""
    try:
        await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL, "to": [user_email],
            "subject": "[ZEKTRIX] Bine ai venit la Zektrix UK!",
            "html": html_content
        })
        logger.info(f"Welcome email sent to {user_email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")


async def send_password_reset_email(user_email: str, username: str, reset_token: str):
    if not RESEND_API_KEY:
        return None
    reset_link = f"https://zektrix.uk/reset-password?token={reset_token}"
    html_content = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;max-width:600px;margin:0 auto;background:#030014;color:white;padding:0;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#8b5cf6,#7c3aed);padding:24px;text-align:center;">
            <h1 style="margin:0;font-size:24px;font-weight:900;"><span style="color:#fff;">ZEKTRIX</span>.UK</h1>
        </div>
        <div style="padding:30px;">
            <h2 style="color:#fff;margin:0 0 16px 0;font-size:20px;">Resetare Parola</h2>
            <p style="color:#9ca3af;font-size:14px;">Salut <strong style="color:#fff;">{username}</strong>,</p>
            <p style="color:#9ca3af;font-size:14px;line-height:1.6;">Am primit o cerere de resetare a parolei pentru contul tau.</p>
            <div style="text-align:center;margin:24px 0;">
                <a href="{reset_link}" style="display:inline-block;background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#fff;text-decoration:none;padding:14px 40px;border-radius:50px;font-weight:700;font-size:14px;">RESETEAZA PAROLA</a>
            </div>
            <p style="color:#6b7280;font-size:12px;">Link valid 1 ora. Daca nu ai cerut resetarea, ignora emailul.</p>
            <div style="text-align:center;border-top:1px solid #1e1b3a;padding-top:16px;margin-top:20px;">
                <p style="color:#4b5563;font-size:10px;margin:0;">&#169; 2026 Zektrix UK Ltd</p>
            </div>
        </div>
    </div>"""
    try:
        email = await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL, "to": [user_email],
            "subject": "[ZEKTRIX] Resetare Parola - Zektrix UK",
            "html": html_content
        })
        logger.info(f"Password reset email sent to {user_email}")
        return email.get("id")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return None


async def send_competition_75_percent_email(user_email: str, username: str, competition_title: str, sold_percent: int):
    if not RESEND_API_KEY:
        return None
    html_content = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;max-width:600px;margin:0 auto;background:#030014;color:white;padding:0;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#ef4444,#f97316);padding:24px;text-align:center;">
            <p style="margin:0;font-size:14px;opacity:0.9;">&#128293; APROAPE SOLD OUT!</p>
            <h1 style="margin:8px 0 0 0;font-size:42px;font-weight:900;">{sold_percent}%</h1>
        </div>
        <div style="padding:30px;">
            <p style="color:#9ca3af;font-size:14px;">Salut <strong style="color:#fff;">{username}</strong>,</p>
            <p style="color:#9ca3af;font-size:14px;line-height:1.6;">Competitia <strong style="color:#fbbf24;">{competition_title}</strong> este aproape terminata!</p>
            <div style="text-align:center;margin:24px 0;">
                <a href="https://zektrix.uk/competitions" style="display:inline-block;background:linear-gradient(135deg,#ef4444,#f97316);color:#fff;text-decoration:none;padding:14px 40px;border-radius:50px;font-weight:700;font-size:14px;">REZERVA-TI LOCUL &#8594;</a>
            </div>
            <div style="text-align:center;border-top:1px solid #1e1b3a;padding-top:16px;">
                <p style="color:#4b5563;font-size:10px;margin:0;">&#169; 2026 Zektrix UK Ltd</p>
            </div>
        </div>
    </div>"""
    try:
        await asyncio.to_thread(resend.Emails.send, {
            "from": SENDER_EMAIL, "to": [user_email],
            "subject": f"[HOT] {sold_percent}% Vandut! {competition_title} - Zektrix UK",
            "html": html_content
        })
    except Exception as e:
        logger.error(f"Failed to send 75% alert email: {str(e)}")
