# -*- coding: utf-8 -*-
"""Chip registry: wordmark lockups, brand palettes and CPU identification.

identify() parses a CPU brand string into vendor / tier / exact model, so the
generator can print the real model number into the wordmark
("CORE i7 / 13700K", "RYZEN 7 / 7800X3D", "\u25cf M 4 / P R O").

Palette slots (all nine are used by every logo):
    $1..$6  die background gradient, darkest -> brightest accent
    $7      pale accent (package rim)
    $8      silver     (lettering)
    $9      bright silver (highlight)

Artwork fields follow the vendors' badge designs:
    apple  radial glow out of the bottom-left corner (Apple keynote die renders)
    intel  horizontal swoosh band, slightly tilted   (Core badge swoosh)
    amd    centred ring                              (Ryzen ring mark)

Palette colours:
    Apple M-series   base = graphite silver, Pro = blue, Max = violet,
                     Ultra = copper (tier colours as rendered in Apple keynotes)
    Intel Core       i3 = sky, i5 = Intel blue #0068B5, i7 = indigo,
                     i9 = carbon black w/ steel-silver
    AMD Ryzen        5 = amber, 7 = Ryzen orange, 9 = AMD red
"""
import platform
import re
import subprocess


def _pal(*hexes):
    return [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in hexes]


PALETTES = {
    "apple-silver": _pal("#121417", "#1E2126", "#363B44", "#525866",
                         "#767E8C", "#A0A8B8", "#C8CFDB", "#E4E9F1", "#FFFFFF"),
    "apple-blue":   _pal("#0A0E1C", "#101A32", "#1A3068", "#264EA8",
                         "#387AD8", "#60A8EC", "#96C4E4", "#C8DEEE", "#F4FAFF"),
    "apple-violet": _pal("#140E20", "#201638", "#3E2A6E", "#5F40AE",
                         "#8A64DC", "#B296EE", "#D2C2F2", "#E7DFF7", "#FBF8FF"),
    "apple-copper": _pal("#1D1208", "#33200E", "#6E4016", "#B06A24",
                         "#DC903C", "#F0B96E", "#F2D8AC", "#F5E8D2", "#FFF9EE"),
    "intel-sky":    _pal("#0A101C", "#0F1C30", "#17345C", "#1F5C9E",
                         "#2E8CD8", "#5FB4EE", "#9CD2F2", "#CDE6F8", "#F0F9FF"),
    "intel-blue":   _pal("#090E1A", "#0E1A30", "#123058", "#0F68B5",
                         "#1E90DE", "#63B6EE", "#9AD0F2", "#D0E6F6", "#F2FAFF"),
    "intel-indigo": _pal("#0A0C1C", "#121632", "#1E2660", "#2E3FAE",
                         "#4B62D8", "#7B8FEC", "#AEB9F2", "#D3DAF6", "#F4F6FF"),
    "intel-carbon": _pal("#0C0D11", "#16181E", "#262931", "#3A3E49",
                         "#5E6B84", "#93A2BC", "#BCBFC9", "#E3E5EA", "#FFFFFF"),
    "amd-amber":    _pal("#1A0E06", "#2E1A0C", "#5C3312", "#9E5A1C",
                         "#D8862A", "#F2AC54", "#F6CE96", "#FAE6C8", "#FFF8EE"),
    "amd-orange":   _pal("#1C0C06", "#321608", "#662A0E", "#A84814",
                         "#D86A1E", "#F2924E", "#F6BC8E", "#FADDC4", "#FFF6EC"),
    "amd-red":      _pal("#1C0A0A", "#320F10", "#641418", "#A81E24",
                         "#DC2830", "#EE5A60", "#F29A9C", "#FAD2D2", "#FFF0F0"),
    # Core Ultra badge: blue -> violet gradient
    "intel-ultra":  _pal("#0B0E1E", "#151A3C", "#27306E", "#3E4CB6",
                         "#6372E2", "#92A4F4", "#C0CBF8", "#E2E7FB", "#F8F9FF"),
    # Xeon: slate / workstation silver
    "intel-xeon":   _pal("#0B0D12", "#151A24", "#242E3E", "#35455E",
                         "#4E6382", "#7E94B2", "#B4C4D6", "#E2EAF2", "#FAFCFF"),
    # Ryzen 3: gold
    "amd-gold":     _pal("#1C1204", "#332408", "#6E4A10", "#B07A1A",
                         "#DCA02E", "#F0C25E", "#F6DC9C", "#FAEECB", "#FFFBEF"),
    # Threadripper: deep rust orange
    "amd-rust":     _pal("#180C05", "#2B1609", "#562E0E", "#944E15",
                         "#C4701E", "#EA9A48", "#F4C48C", "#F9E2C6", "#FFF6EA"),
    # EPYC: datacenter teal
    "amd-teal":     _pal("#07110C", "#0C2016", "#13442C", "#1A6E44",
                         "#24A060", "#46C886", "#8EE2B4", "#C4F0D6", "#EFFAF2"),
}

# vendor -> die artwork style (see module docstring)
FAMILY_FIELDS = {"apple": "glow", "intel": "band", "amd": "ring"}

CHIPS = {}


def _apple(gen, tiers):
    for suffix, tier, line2, palette in tiers:
        cid = "m%d%s" % (gen, suffix)
        CHIPS[cid] = dict(
            label="Apple M%d%s" % (gen, " " + tier if tier else ""),
            family="apple",
            line1="\u25cf M %d" % gen,
            line2=line2,
            palette=palette,
            # base tier is checked last: "apple m4" also matches "apple m4 pro"
            match=[r"apple\s+m%d\s+%s" % (gen, suffix)] if suffix
                  else [r"apple\s+m%d\b" % gen],
        )


# ordered: ultra/max/pro before the base tier (first regex match wins)
_apple(1, [("ultra", "Ultra", "U L T R A", "apple-copper"),
           ("max", "Max", "M A X", "apple-violet"),
           ("pro", "Pro", "P R O", "apple-blue"),
           ("", "", "", "apple-silver")])
_apple(2, [("ultra", "Ultra", "U L T R A", "apple-copper"),
           ("max", "Max", "M A X", "apple-violet"),
           ("pro", "Pro", "P R O", "apple-blue"),
           ("", "", "", "apple-silver")])
_apple(3, [("ultra", "Ultra", "U L T R A", "apple-copper"),
           ("max", "Max", "M A X", "apple-violet"),
           ("pro", "Pro", "P R O", "apple-blue"),
           ("", "", "", "apple-silver")])
_apple(4, [("max", "Max", "M A X", "apple-violet"),
           ("pro", "Pro", "P R O", "apple-blue"),
           ("", "", "", "apple-silver")])
_apple(5, [("ultra", "Ultra", "U L T R A", "apple-copper"),
           ("max", "Max", "M A X", "apple-violet"),
           ("pro", "Pro", "P R O", "apple-blue"),
           ("", "", "", "apple-silver")])
_apple(6, [("", "", "", "apple-silver")])

for n in (9, 7, 5):
    CHIPS["ultra%d" % n] = dict(
        label="Intel Core Ultra %d" % n,
        family="intel",
        line1="intel",
        line2="CORE ULTRA %d" % n,
        palette="intel-ultra",
        match=[r"core\s+ultra\s+%d\b" % n],
    )

CHIPS["xeon"] = dict(
    label="Intel Xeon",
    family="intel",
    line1="intel",
    line2="XEON",
    palette="intel-xeon",
    match=[r"xeon"],
)

for n, pal in ((9, "intel-carbon"), (7, "intel-indigo"),
               (5, "intel-blue"), (3, "intel-sky")):
    CHIPS["i%d" % n] = dict(
        label="Intel Core i%d" % n,
        family="intel",
        line1="intel",
        line2="CORE i%d" % n,
        palette=pal,
        match=[r"core\s*\(tm\)\s*i%d\b" % n, r"\bi%d-\d" % n],
    )

CHIPS["threadripper"] = dict(
    label="AMD Ryzen Threadripper",
    family="amd",
    line1="AMD",
    line2="THREADRIPPER",
    palette="amd-rust",
    match=[r"threadripper"],
)

CHIPS["epyc"] = dict(
    label="AMD EPYC",
    family="amd",
    line1="AMD",
    line2="EPYC",
    palette="amd-teal",
    match=[r"epyc"],
)

for n, pal in ((9, "amd-red"), (7, "amd-orange"),
               (5, "amd-amber"), (3, "amd-gold")):
    CHIPS["ryzen%d" % n] = dict(
        label="AMD Ryzen %d" % n,
        family="amd",
        line1="AMD",
        line2="RYZEN %d" % n,
        palette=pal,
        match=[r"ryzen\s*%d\b" % n],
    )


def normalize(s):
    s = re.sub(r"\((r|tm)\)|[\u00ae\u2122]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def identify(brand=None):
    """Parse a CPU brand string.

    Returns dict(chip_id, family, tier, model, label) or None.
    `model` keeps the original case ("13700K", "7800X3D", "155H").
    """
    if brand is None:
        brand = host_cpu_name()
    raw = brand or ""
    n = normalize(raw)
    chip_id = None
    for cid, spec in CHIPS.items():
        if any(re.search(p, n) for p in spec["match"]):
            chip_id = cid
            break
    if chip_id is None:
        return None
    spec = CHIPS[chip_id]
    info = dict(chip_id=chip_id, family=spec["family"], tier=None,
                model=None, label=spec["label"])

    if spec["family"] == "apple":
        m = re.search(r"apple\s+m(\d)\s*(pro|max|ultra)?", n)
        if m:
            info["tier"] = m.group(2) or ""
            info["model"] = "M%s%s" % (m.group(1),
                                       " " + m.group(2).title() if m.group(2) else "")
    elif spec["family"] == "intel":
        if chip_id == "xeon":
            m = re.search(r"xeon\s*(?:\(r\))?\s*([A-Za-z]-\d{4}\w*|\d{4}\w*)",
                          raw, re.I)
            if m:
                info["tier"] = "xeon"
                info["model"] = m.group(1).upper()
        else:
            m = re.search(r"core\s*(?:\(tm\))?\s+(ultra\s+)?(i)?([3579])[-\s](\w+)",
                          raw, re.I)
            if m:
                info["tier"] = ("ultra" if m.group(1) else "i") + m.group(3)
                info["model"] = m.group(4).upper()
    elif spec["family"] == "amd":
        if chip_id == "threadripper":
            m = re.search(r"threadripper\s*(?:pro\s+)?(\d{4}\w*)", raw, re.I)
            if m:
                info["tier"] = "tr"
                info["model"] = m.group(1).upper()
        elif chip_id == "epyc":
            m = re.search(r"epyc\s+(\w+)", raw, re.I)
            if m:
                info["tier"] = "epyc"
                info["model"] = m.group(1).upper()
        else:
            m = re.search(r"ryzen\s+([3579])\s+(\w+)", raw, re.I)
            if m:
                info["tier"] = m.group(1)
                info["model"] = m.group(2).upper()
    return info


def wordmark(info):
    """(line1, line2) for an identify() result; falls back to the generic
    registry lockup when the exact model could not be parsed."""
    spec = CHIPS[info["chip_id"]]
    fam, model = info["family"], info["model"]
    if fam == "apple":
        return spec["line1"], spec["line2"]
    if fam == "intel":
        if info["tier"] and info["tier"].startswith("ultra"):
            return "CORE ULTRA " + info["tier"][-1], model or ""
        if info["tier"] == "xeon":
            return ("XEON", model) if model else (spec["line1"], spec["line2"])
        if model:
            return "CORE i" + info["tier"][-1], model
        return spec["line1"], spec["line2"]
    if fam == "amd":
        if info["tier"] == "tr":
            return ("THREADRIPPER", model) if model else (spec["line1"], spec["line2"])
        if info["tier"] == "epyc":
            return ("AMD EPYC", model) if model else (spec["line1"], spec["line2"])
        if model:
            return "RYZEN " + info["tier"], model
        return spec["line1"], spec["line2"]
    return spec["line1"], spec["line2"]


def detect(brand=None):
    """Map a CPU brand string to a generic chip id; None when nothing matches."""
    info = identify(brand)
    return info["chip_id"] if info else None


def host_cpu_name():
    if platform.system() == "Darwin":
        try:
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        except Exception:
            return ""
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return ""
