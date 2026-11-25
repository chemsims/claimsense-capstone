"""Draws docs/diagrams/architecture.svg. Hand-placed so every flow label is readable.
Run: python scripts/draw_architecture.py"""
from pathlib import Path

W, H = 1600, 1000
BLUE, BLUE_BG, ORANGE, ORANGE_BG = "#1d4ed8", "#dbeafe", "#c2410c", "#ffedd5"
GREY, GREY_BG, RED, INK = "#475569", "#f1f5f9", "#dc2626", "#0f172a"
out: list[str] = []


def box(x, y, w, h, lines, stroke, fill, bold_first=True, rx=8, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"{d}/>')
    n = len(lines)
    for i, t in enumerate(lines):
        ty = y + h / 2 + (i - (n - 1) / 2) * 17 + 5
        wgt = "700" if (i == 0 and bold_first) else "400"
        size = 14 if i == 0 else 12
        out.append(f'<text x="{x + w / 2}" y="{ty}" text-anchor="middle" font-size="{size}" font-weight="{wgt}" fill="{INK}">{t}</text>')


def store(x, y, w, h, lines):
    box(x, y, w, h, lines, GREY, GREY_BG, rx=18)


def arrow(pts, label=None, lx=None, ly=None, color=INK, width=1.6, dash=None, anchor="middle", both=False):
    d = "M " + " L ".join(f"{a},{b}" for a, b in pts)
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    ms = ' marker-start="url(#a)"' if both else ""
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{ds} marker-end="url(#a)"{ms}/>')
    if label:
        for i, t in enumerate(label.split("|")):
            tw = len(t) * 6.4 + 6
            rx0 = {"middle": lx - tw / 2, "start": lx - 3, "end": lx - tw + 3}[anchor]
            out.append(f'<rect x="{rx0}" y="{ly + i * 14 - 11}" width="{tw}" height="14" fill="white" opacity="0.92"/>')
            out.append(f'<text x="{lx}" y="{ly + i * 14}" text-anchor="{anchor}" font-size="12" fill="{INK}">{t}</text>')


out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           'font-family="Inter, Helvetica, Arial, sans-serif">')
out.append('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0f172a"/></marker></defs>')
out.append(f'<rect width="{W}" height="{H}" fill="white"/>')
out.append(f'<text x="20" y="34" font-size="22" font-weight="700" fill="{INK}">ClaimSense co-pilot · solution architecture</text>')
out.append(f'<text x="20" y="56" font-size="13" fill="{GREY}">All flows numbered F1–F24 (table in ARCHITECTURE.md). Solid = read · thick = write · dashed = refusal or human action</text>')

# Lanes
out.append(f'<rect x="190" y="74" width="1400" height="196" rx="12" fill="#fff7ed" stroke="{ORANGE}" stroke-width="2.5" stroke-dasharray="8 4"/>')
out.append(f'<text x="205" y="96" font-size="15" font-weight="700" fill="{ORANGE}">MODEL JUDGMENT · OpenAI Agents SDK · strict typed outputs · every judgment cites evidence</text>')
out.append(f'<rect x="190" y="320" width="1400" height="190" rx="12" fill="#eff6ff" stroke="{BLUE}" stroke-width="2.5"/>')
out.append(f'<text x="205" y="500" font-size="15" font-weight="700" fill="{BLUE}">DETERMINISTIC CODE · Python FastAPI on ECS Fargate · identity, access, dates, money, joins, validation</text>')
# Boundary line
out.append(f'<line x1="190" y1="295" x2="1590" y2="295" stroke="{RED}" stroke-width="3" stroke-dasharray="14 6"/>')
out.append(f'<text x="200" y="314" font-size="13" font-weight="700" fill="{RED}">CODE ↔ MODEL BOUNDARY · only typed objects cross · the model never sees identity, never writes</text>')

# Model lane boxes
box(210, 120, 170, 70, ["Secrets Manager", "OpenAI API key"], GREY, GREY_BG)
store(420, 115, 180, 80, ["Clause index (S3)", "14 synthetic clauses", "SearchClauses tool"])
box(640, 110, 220, 90, ["Coverage agent", "Does the clause wording", "cover this loss?"], ORANGE, ORANGE_BG)
box(900, 110, 220, 90, ["Consistency / fraud agent", "Does the story hold", "across documents?"], ORANGE, ORANGE_BG)
box(1160, 110, 210, 90, ["Decision drafter", "APPROVE · DENY · FLAG", "· ROUTE_SIU + reasons"], ORANGE, ORANGE_BG)
box(1420, 120, 150, 70, ["OpenAI API", "gpt-4o-mini"], GREY, GREY_BG)

# Code lane boxes
Y, BH = 360, 110
box(20, 375, 140, 80, ["Adjuster", "web UI"], INK, "white")
box(200, Y, 190, BH, ["① AuthN", "verify Cognito JWT", "→ user_id, roles"], BLUE, BLUE_BG)
box(420, Y, 190, BH, ["② Access layer", "entitlement check", "BEFORE any agent runs"], BLUE, BLUE_BG)
box(640, Y, 190, BH, ["③ Data gateway", "join claim→policy→docs", "drop PII · flag injection"], BLUE, BLUE_BG)
box(860, Y, 190, BH, ["④ Fact engine", "in force on loss date · VIN", "deductible · payout · ratio", "missing evidence"], BLUE, BLUE_BG)
box(1080, Y, 190, BH, ["⑤ Decision guard", "schema + citation check", "hard rules · provenance", "fallback = FLAG"], BLUE, BLUE_BG)
box(1300, Y, 190, BH, ["⑥ CMS writer", "idempotency key =", "sha256(claim|inputs|version)"], BLUE, BLUE_BG)

# Bottom row
out.append(f'<rect x="405" y="645" width="660" height="140" rx="12" fill="none" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="4 4"/>')
out.append(f'<text x="530" y="774" font-size="13" font-weight="700" fill="{GREY}">CLIENT SYSTEMS (synthetic stubs in the pilot)</text>')
store(200, 680, 170, 70, ["Cognito", "user pool"])
store(420, 660, 190, 80, ["Claims Mgmt (CMS)", "read claim + assignment", "write draft only"])
store(645, 660, 190, 80, ["Policy Admin (PAS)", "read only"])
store(865, 660, 185, 80, ["Document store", "read only · OCR text"])
store(1100, 670, 170, 80, ["Audit log", "DynamoDB", "append-only"])
store(1300, 670, 190, 80, ["CloudWatch", "logs · p95 · errors", "+ 1 alarm"])

# Flows
arrow([(160, 405), (198, 405)], "F1", 179, 398)
arrow([(295, 470), (295, 678)], "F2 verify token", 290, 625, anchor="end")
arrow([(390, 415), (418, 415)], "F3", 404, 408)
arrow([(450, 470), (450, 658)], "F4 GetAssignment", 444, 600, anchor="end")
arrow([(515, 360), (515, 336), (90, 336), (90, 373)], "F5 DENIED → 403, zero claim data, audited", 300, 330, dash="6 4", color=RED)
arrow([(610, 415), (638, 415)], "F6", 624, 408)
arrow([(690, 470), (530, 658)], "F7 GetClaim", 536, 640, anchor="end")
arrow([(735, 470), (735, 658)], "F8 GetPolicy|(no holder name)", 742, 610, anchor="start")
arrow([(790, 470), (930, 658)], "F9 List+GetText|(untrusted text)", 905, 615, anchor="start")
arrow([(830, 415), (858, 415)], "F10", 844, 408)
arrow([(925, 360), (760, 202)], "F11 facts (read-only)|+ evidence bundle", 760, 262, anchor="end")
arrow([(985, 360), (1005, 202)], "F11", 1004, 343, anchor="start")
arrow([(640, 155), (602, 155)], "F12", 621, 148)
arrow([(830, 200), (830, 232), (1230, 232), (1230, 202)], "F13 coverage judgment + clause_ids", 1110, 252)
arrow([(1120, 155), (1158, 155)], "F13", 1139, 148)
arrow([(1370, 155), (1418, 155)], "F14", 1394, 148, both=True)
arrow([(1290, 200), (1200, 358)], "F15 typed draft", 1262, 286, anchor="start")
arrow([(1050, 440), (1078, 440)], "F16", 1064, 455)
arrow([(1270, 415), (1298, 415)], "F17", 1284, 408)
arrow([(1395, 470), (1395, 580), (592, 580), (592, 658)], "F18 PutRecommendation (WRITE, idempotent)", 1180, 575, width=3.5)
arrow([(1140, 470), (1140, 535), (110, 535), (110, 457)], "F19 decision · reasons · citations · each field labelled code or model", 760, 530)
arrow([(50, 457), (50, 840), (515, 840), (515, 742)], "F20 adjuster confirms / overrides in CMS (human; only this changes claim status)", 60, 858, anchor="start", dash="6 4")
arrow([(1185, 510), (1185, 668)], "F21 every call,|granted or denied", 1192, 620, anchor="start")
arrow([(1440, 510), (1440, 668)], "F22 traces,|metrics", 1447, 620, anchor="start")
arrow([(295, 190), (295, 318)], "F23 key at startup", 300, 250, anchor="start")

# CI + legend
box(1100, 800, 470, 80, ["F24 · CI (GitHub Actions)", "commit → 150-case eval gate → push image to ECR only if it passes", "→ deploy to ECS"], INK, "white")
lx, ly = 20, 900
out.append(f'<rect x="{lx}" y="{ly}" width="22" height="14" fill="{BLUE_BG}" stroke="{BLUE}"/><text x="{lx+30}" y="{ly+12}" font-size="13">deterministic code (tested, no model)</text>')
out.append(f'<rect x="{lx+290}" y="{ly}" width="22" height="14" fill="{ORANGE_BG}" stroke="{ORANGE}"/><text x="{lx+320}" y="{ly+12}" font-size="13">model judgment (must cite)</text>')
out.append(f'<rect x="{lx+520}" y="{ly}" width="22" height="14" fill="{GREY_BG}" stroke="{GREY}"/><text x="{lx+550}" y="{ly+12}" font-size="13">data store / external service</text>')
out.append(f'<text x="{lx}" y="{ly+44}" font-size="13" fill="{GREY}">Synthetic data only. Agents call no client system directly: the SearchClauses tool runs in code and returns only retrieved clause IDs.</text>')
out.append("</svg>")

p = Path(__file__).resolve().parents[1] / "docs" / "diagrams" / "architecture.svg"
p.write_text("\n".join(out))
print("wrote", p)
