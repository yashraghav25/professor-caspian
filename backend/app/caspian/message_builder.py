"""
Professional alert message templates for Caspian delivery.
Structured output — not free-form LLM slop.
"""

from __future__ import annotations

import re
from html import escape

from app.models.alert import Alert
from caspian_sdk.blocks import bullet_list, divider, heading, text as text_block


def _parse_sections(ai_summary: str | None) -> dict[str, str]:
    """Extract What happened / Portfolio impact / Suggested actions from agent output."""
    text = ai_summary or ""
    sections = {"what": "", "impact": "", "actions": ""}

    patterns = [
        (r"\*\*What happened\*\*\s*(.*?)(?=\*\*Portfolio impact\*\*|\*\*Suggested actions\*\*|$)", "what"),
        (r"\*\*Portfolio impact\*\*\s*(.*?)(?=\*\*Suggested actions\*\*|$)", "impact"),
        (r"\*\*Suggested actions\*\*\s*(.*?)$", "actions"),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            sections[key] = m.group(1).strip()

    if not sections["what"]:
        sections["what"] = text.split("\n\n")[0][:280] if text else "A significant market event affected your portfolio."
    if not sections["actions"]:
        sections["actions"] = "Review affected positions and confirm your risk limits."

    return sections


def _severity_label(level: str) -> str:
    return level.upper() if level else "ALERT"


def build_email_subject(alert: Alert) -> str:
    """Clear inbox subject line."""
    title = alert.title or "Portfolio Alert"
    # Strip redundant severity prefix if already in title
    for prefix in ("WARNING:", "HIGH:", "CRITICAL:", "WARNING", "HIGH", "CRITICAL"):
        if title.upper().startswith(prefix):
            title = title[len(prefix):].strip(" :-")
            break
    return f"[SentinelAI] {_severity_label(str(alert.severity_level.value))} — {title[:60]}"


def build_email_plain(alert: Alert) -> str:
    sections = _parse_sections(alert.ai_summary)
    sev = _severity_label(str(alert.severity_level.value))
    return (
        f"SentinelAI Portfolio Alert\n"
        f"Severity: {sev}  ·  Score: {alert.severity_score:.0f}/100\n\n"
        f"What happened\n{sections['what']}\n\n"
        f"Portfolio impact\n{sections['impact'] or 'See holdings in your dashboard.'}\n\n"
        f"Recommended action\n{sections['actions']}\n\n"
        f"—\nReply ACK to dismiss this alert."
    )


def build_email_html(alert: Alert) -> str:
    sections = _parse_sections(alert.ai_summary)
    sev = _severity_label(str(alert.severity_level.value))
    sev_color = {"CRITICAL": "#dc2626", "HIGH": "#ea580c", "WARNING": "#ca8a04"}.get(sev, "#2563eb")

    what = escape(sections["what"])
    impact = escape(sections["impact"]) or "Check your dashboard for live holdings and P/L."
    actions = escape(sections["actions"])
    title = escape(alert.title or "Portfolio Alert")

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f4f4f5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;border:1px solid #e4e4e7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <tr><td style="padding:24px 28px 16px;border-bottom:1px solid #e4e4e7;">
    <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;color:#71717a;text-transform:uppercase;">SentinelAI</div>
    <div style="font-size:20px;font-weight:600;color:#18181b;margin-top:6px;">{title}</div>
    <div style="margin-top:10px;">
      <span style="display:inline-block;padding:3px 10px;border-radius:4px;font-size:12px;font-weight:600;color:#fff;background:{sev_color};">{sev}</span>
      <span style="font-size:13px;color:#71717a;margin-left:8px;">Score {alert.severity_score:.0f}/100</span>
    </div>
  </td></tr>
  <tr><td style="padding:20px 28px;">
    <div style="font-size:12px;font-weight:600;color:#71717a;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">What happened</div>
    <div style="font-size:15px;line-height:1.55;color:#27272a;margin-bottom:20px;">{what}</div>
    <div style="font-size:12px;font-weight:600;color:#71717a;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">Portfolio impact</div>
    <div style="font-size:15px;line-height:1.55;color:#27272a;margin-bottom:20px;">{impact}</div>
    <div style="font-size:12px;font-weight:600;color:#71717a;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">Recommended action</div>
    <div style="font-size:15px;line-height:1.55;color:#27272a;">{actions}</div>
  </td></tr>
  <tr><td style="padding:16px 28px 24px;border-top:1px solid #e4e4e7;">
    <div style="font-size:12px;color:#a1a1aa;">Reply <strong>ACK</strong> to dismiss · Automated portfolio monitoring</div>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>"""


def build_telegram_text(alert: Alert) -> str:
    """Instant alert — under 280 chars, no markdown."""
    sections = _parse_sections(alert.ai_summary)
    sev = _severity_label(str(alert.severity_level.value))
    icon = "🚨" if sev == "CRITICAL" else "⚠️"

    # One-line headline from title
    headline = alert.title or "Portfolio alert"
    for prefix in ("WARNING:", "HIGH:", "CRITICAL:"):
        if headline.upper().startswith(prefix):
            headline = headline[len(prefix):].strip()

    action_line = sections["actions"].split("\n")[0]
    action_line = re.sub(r"^\d+\.\s*", "", action_line)[:90]

    msg = (
        f"{icon} {sev} ALERT\n"
        f"{headline[:80]}\n"
        f"{sections['what'][:100]}\n"
        f"→ {action_line}\n"
        f"Reply ACK to dismiss"
    )
    return msg[:400]


def build_rich_blocks(markdown: str) -> list[dict]:
    """Turn SentinelAI's compact Markdown into Caspian native blocks.

    Caspian renders these natively in Telegram, with a clean plain-text fallback
    on less capable channels.
    """
    blocks: list[dict] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_ordered = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(text_block("\n".join(paragraph)))
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            blocks.append(bullet_list(list_items, ordered=list_ordered))
            list_items = []

    for raw_line in (markdown or "").splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            flush_paragraph()
            flush_list()
            blocks.append(heading(line[2:-2]))
            continue
        ordered_match = re.match(r"^\d+\.\s+(.+)$", line)
        bullet_match = re.match(r"^[-*]\s+(.+)$", line)
        if ordered_match or bullet_match:
            flush_paragraph()
            is_ordered = bool(ordered_match)
            if list_items and list_ordered != is_ordered:
                flush_list()
            list_ordered = is_ordered
            list_items.append((ordered_match or bullet_match).group(1))
            continue
        flush_list()
        paragraph.append(line)

    flush_paragraph()
    flush_list()
    return blocks or [text_block("SentinelAI update")]


def build_telegram_blocks(alert: Alert) -> list[dict]:
    """Structured version of an alert for native Telegram rendering."""
    sections = _parse_sections(alert.ai_summary)
    sev = _severity_label(str(alert.severity_level.value))
    return [
        heading(f"{'🚨' if sev == 'CRITICAL' else '⚠️'} {sev} ALERT"),
        text_block(alert.title or "Portfolio alert"),
        divider(),
        heading("What happened"),
        text_block(sections["what"]),
        heading("Suggested action"),
        text_block(sections["actions"]),
        text_block("Reply WHY for evidence · DETAILS for the full brief · ACK to acknowledge"),
    ]


def build_daily_report_html(subject: str, body_plain: str) -> tuple[str, str]:
    """Format end-of-day digest."""
    lines = [l.strip() for l in body_plain.split("\n") if l.strip()]
    body_html = "".join(
        f'<p style="margin:0 0 12px;font-size:15px;line-height:1.55;color:#27272a;">{escape(l)}</p>'
        for l in lines
    )
    html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f4f4f5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;border:1px solid #e4e4e7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <tr><td style="padding:24px 28px 16px;border-bottom:1px solid #e4e4e7;">
    <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;color:#71717a;text-transform:uppercase;">SentinelAI Daily Report</div>
    <div style="font-size:18px;font-weight:600;color:#18181b;margin-top:6px;">{escape(subject)}</div>
  </td></tr>
  <tr><td style="padding:20px 28px;">{body_html}</td></tr>
  <tr><td style="padding:16px 28px 24px;border-top:1px solid #e4e4e7;">
    <div style="font-size:12px;color:#a1a1aa;">End-of-day portfolio summary · SentinelAI</div>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>"""
    return subject, html


def build_escalation_email(alert: Alert, overdue_seconds: int) -> tuple[str, str, str]:
    """Build a distinct follow-up when a material incident has no acknowledgement."""
    sections = _parse_sections(alert.ai_summary)
    minutes = max(1, overdue_seconds // 60)
    subject = f"[ACTION REQUIRED] SentinelAI incident not acknowledged — {alert.title[:55]}"
    plain = (
        f"SentinelAI escalation\n\n"
        f"A {str(alert.severity_level.value).lower()} incident has not been acknowledged after {minutes} minutes.\n\n"
        f"Incident: {alert.title}\n"
        f"Evidence: {alert.reason or sections['what']}\n\n"
        "Reply ACK to confirm that this incident has been seen."
    )
    html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f4f4f5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 0;"><tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;border:1px solid #fecaca;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <tr><td style="padding:24px 28px;background:#991b1b;border-radius:8px 8px 0 0;color:#fff;">
    <div style="font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.8;">SentinelAI escalation</div>
    <div style="font-size:20px;font-weight:650;margin-top:6px;">Action required</div>
  </td></tr>
  <tr><td style="padding:24px 28px;color:#27272a;">
    <p style="margin:0 0 16px;font-size:15px;line-height:1.55;">A <strong>{escape(str(alert.severity_level.value).lower())}</strong> incident has not been acknowledged after {minutes} minutes.</p>
    <div style="padding:14px 16px;background:#fef2f2;border-left:3px solid #dc2626;border-radius:4px;margin-bottom:18px;">
      <div style="font-size:15px;font-weight:600;">{escape(alert.title)}</div>
      <div style="font-size:13px;color:#52525b;margin-top:6px;">Score {alert.severity_score:.0f}/100</div>
    </div>
    <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#71717a;margin-bottom:6px;">Why SentinelAI escalated</div>
    <div style="font-size:15px;line-height:1.55;">{escape(alert.reason or sections['what'])}</div>
  </td></tr>
  <tr><td style="padding:16px 28px 24px;border-top:1px solid #e4e4e7;font-size:13px;color:#52525b;">Reply <strong>ACK</strong> to confirm this incident has been seen.</td></tr>
</table></td></tr></table>
</body></html>"""
    return subject, plain, html
