#!/usr/bin/env python3
"""Convert Mermaid sequence diagrams to Draw.io UML sequence diagrams.

Usage:
    python scripts/mermaid2drawio.py input.mmd -o output.drawio
    python scripts/mermaid2drawio.py input.mmd                    # output.drawio
    cat diagram.mmd | python scripts/mermaid2drawio.py > out.drawio

Supports:
    - participant / actor declarations
    - Solid arrows (->>) and dashed arrows (-->>)
    - Activation (+B / -B on arrows, or explicit activate/deactivate)
    - Notes (over, left of, right of)
    - Loop / alt / opt fragments
    - autonumber (ignored gracefully)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

# ── Intermediate Representation ──────────────────────────────────────────────

class Participant:
    __slots__ = ("id", "label", "actor")
    def __init__(self, id: str, label: str | None = None, actor: bool = False):
        self.id = id
        self.label = label or id
        self.actor = actor

class Message:
    """A message arrow."""
    __slots__ = ("source", "target", "label", "dashed", "activate_target", "deactivate_source")
    def __init__(self, source: str, target: str, label: str = "",
                 dashed: bool = False,
                 activate_target: bool = False,
                 deactivate_source: bool = False):
        self.source = source
        self.target = target
        self.label = label
        self.dashed = dashed
        self.activate_target = activate_target
        self.deactivate_source = deactivate_source

class Fragment:
    """Grouping fragment like loop, alt, opt."""
    __slots__ = ("kind", "condition")
    def __init__(self, kind: str, condition: str = ""):
        self.kind = kind   # "loop", "alt", "else", "opt", "rect"
        self.condition = condition

class Note:
    __slots__ = ("position", "targets", "text")
    def __init__(self, position: str, targets: list[str], text: str):
        self.position = position   # "over", "left", "right"
        self.targets = targets
        self.text = text

class Activate:
    __slots__ = ("target",)
    def __init__(self, target: str):
        self.target = target

class Deactivate:
    __slots__ = ("target",)
    def __init__(self, target: str):
        self.target = target

# ── Parser ───────────────────────────────────────────────────────────────────

def parse_mermaid(text: str):
    """Parse Mermaid sequence diagram text into an ordered list of events."""
    participants: dict[str, Participant] = {}
    events: list = []
    seen_participants: set[str] = set()
    autonumber = False
    in_sequence = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue

        # Skip diagram type declaration
        if stripped.lower().startswith("sequencediagram"):
            in_sequence = True
            continue

        if not in_sequence:
            continue

        # ── participant / actor declarations ──
        m = re.match(r"participant\s+(\S+)(?:\s+as\s+(.+))?$", stripped, re.IGNORECASE)
        if m:
            pid = m.group(1)
            label = (m.group(2) or "").strip() or pid
            participants[pid] = Participant(pid, label)
            seen_participants.add(pid)
            continue

        m = re.match(r"actor\s+(\S+)(?:\s+as\s+(.+))?$", stripped, re.IGNORECASE)
        if m:
            pid = m.group(1)
            label = (m.group(2) or "").strip() or pid
            participants[pid] = Participant(pid, label, actor=True)
            seen_participants.add(pid)
            continue

        # ── autonumber ──
        if stripped.lower().startswith("autonumber"):
            autonumber = True
            continue

        # ── activate / deactivate ──
        m = re.match(r"activate\s+(\S+)", stripped, re.IGNORECASE)
        if m:
            events.append(Activate(m.group(1)))
            seen_participants.add(m.group(1))
            continue

        m = re.match(r"deactivate\s+(\S+)", stripped, re.IGNORECASE)
        if m:
            events.append(Deactivate(m.group(1)))
            seen_participants.add(m.group(1))
            continue

        # ── Messages:  A->>B: text  or  A-->>B: text  or  A->>+B: text  or  A-->>-B: text
        # Source uses non-greedy (\S+?) so B-->> is parsed as B + -->> not B- + ->>.
        # Target uses [^\s:]+ to prevent eating the colon separator.
        m = re.match(
            r"(\S+?)\s*(->>|-->>)([+\-])?\s*([^\s:]+)(?:\s*:\s*(.*))?$",
            stripped,
        )
        if m:
            source = m.group(1)
            arrow = m.group(2)   # "->>" or "-->>"
            act_marker = m.group(3)  # "+" or "-" or None
            target = m.group(4)
            label = (m.group(5) or "").strip()

            dashed = arrow == "-->>"
            activate_target = act_marker == "+"
            deactivate_source = act_marker == "-"

            events.append(Message(source, target, label, dashed,
                                  activate_target, deactivate_source))
            seen_participants.add(source)
            seen_participants.add(target)
            continue

        # Also match arrow variants like ->> without +/- suffix
        m = re.match(
            r"(\S+?)\s*(->>|-->>)\s*([^\s:]+)(?:\s*:\s*(.*))?$",
            stripped,
        )
        if m:
            source = m.group(1)
            arrow = m.group(2)
            target = m.group(3)
            label = (m.group(4) or "").strip()
            dashed = arrow == "-->>"
            events.append(Message(source, target, label, dashed))
            seen_participants.add(source)
            seen_participants.add(target)
            continue

        # ── Notes ──
        m = re.match(r"Note\s+(over|left of|right of)\s+(\S+(?:\s*,\s*\S+)*)\s*:\s*(.*)", stripped)
        if m:
            position = m.group(1)
            targets_raw = m.group(2)
            text = m.group(3).strip()
            targets = [t.strip() for t in targets_raw.split(",")]
            events.append(Note(position, targets, text))
            for t in targets:
                seen_participants.add(t)
            continue

        # ── Loop / alt / opt / rect ──
        m = re.match(r"(loop|alt|else|opt)\s*(.*)", stripped, re.IGNORECASE)
        if m:
            kind = m.group(1).lower()
            condition = m.group(2).strip()
            events.append(Fragment(kind, condition))
            continue

        m = re.match(r"rect\s+(.+)$", stripped, re.IGNORECASE)
        if m:
            events.append(Fragment("rect", m.group(1).strip()))
            continue

        # ── end ──
        if stripped.lower() == "end":
            events.append(Fragment("end"))
            continue

    # Auto-register any seen participants not explicitly declared
    for pid in seen_participants:
        if pid not in participants:
            participants[pid] = Participant(pid)

    return list(participants.values()), events


# ── Draw.io XML Generator ────────────────────────────────────────────────────

# Layout constants
PARTICIPANT_W = 80       # width of participant lifeline
PARTICIPANT_H = 500      # total height (covers all interactions)
PARTICIPANT_GAP = 160    # horizontal gap between participants
START_X = 100            # first participant X
HEADER_Y = 60            # participant header Y
FIRST_MESSAGE_Y = 120    # first message Y
MESSAGE_STEP = 50        # vertical step per message / event
LIFELINE_PAD = 40        # extra space after last message
ACTIVATION_W = 24        # width of activation bar
NOTE_W = 160             # width of note box
NOTE_H = 50              # height of note box

# Colors
LOOP_COLOR = "#E8F5E9"
ALT_COLOR = "#FFF3E0"
OPT_COLOR = "#E3F2FD"
RECT_COLOR = "#F3E5F5"
ACTIVATION_FILL = "#d4e1f5"


def _cell_id(prefix: str, index: int) -> str:
    return f"{prefix}{index}"


def _participant_index(participants: list[Participant], pid: str) -> int:
    for i, p in enumerate(participants):
        if p.id == pid:
            return i
    return 0


def generate_drawio_xml(participants: list[Participant], events: list) -> str:
    """Generate the full .drawio XML string."""
    ns = "http://www.w3.org/2000/svg"  # not used but standard in drawio

    mxfile = ET.Element("mxfile", host="Hermes mermaid2drawio")
    diagram = ET.SubElement(mxfile, "diagram", name="Sequence Diagram")

    model = ET.SubElement(
        diagram, "mxGraphModel",
        dx="0", dy="0", grid="1", gridSize="10",
        guides="1", tooltips="1", connect="1",
        arrows="1", fold="1", page="1", pageScale="1",
        pageWidth="827", pageHeight="1169", math="0", shadow="0",
    )

    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # ── Cell counters ──
    cid = [2]  # mutable counter for cell IDs

    def next_id() -> str:
        n = cid[0]
        cid[0] += 1
        return str(n)

    # Map: participant_id -> lifeline cell id
    p_cells: dict[str, str] = {}

    # ── Create lifeline for each participant ──
    total_h = max(
        HEADER_Y + len(events) * MESSAGE_STEP + LIFELINE_PAD + 100,
        PARTICIPANT_H,
    )

    for idx, p in enumerate(participants):
        cell_id_str = next_id()
        x = START_X + idx * PARTICIPANT_GAP
        p_cells[p.id] = cell_id_str

        label = _escape_xml(p.label)
        style = (
            "shape=umlLifeline;"
            "perimeter=orthogonalLifelinePerimeter;"
            "whiteSpace=wrap;html=1;"
            "container=1;collapsible=0;recursiveResize=0;"
            "strokeWidth=2;fontStyle=1;"
        )
        ET.SubElement(
            root, "mxCell",
            id=cell_id_str,
            value=label,
            style=style,
            vertex="1", parent="1",
        ).append(
            ET.Element("mxGeometry",
                       x=str(x), y=str(HEADER_Y),
                       width=str(PARTICIPANT_W), height=str(total_h),
                       as_="geometry")
        )

    # ── Process events, building draw.io elements ──
    # Track activation state: participant_id -> activation bar cell id or None
    active_bars: dict[str, str] = {}

    # Track current Y position
    current_y = FIRST_MESSAGE_Y

    # Fragment stack for loop/alt/opt nesting
    fragment_stack: list[dict] = []  # each entry: {kind, condition, start_y, start_event, cell_id}
    fragment_counter = [0]

    # Track messages for auto-numbering
    msg_counter = [0]

    for event in events:
        if isinstance(event, Message):
            msg_counter[0] += 1
            src_idx = _participant_index(participants, event.source)
            tgt_idx = _participant_index(participants, event.target)
            src_x = START_X + src_idx * PARTICIPANT_GAP
            tgt_x = START_X + tgt_idx * PARTICIPANT_GAP

            # Determine which cells to connect
            source_cell = active_bars.get(event.source, p_cells[event.source])
            target_cell = active_bars.get(event.target, p_cells[event.target])

            # Handle +B (activate target) and -B (deactivate source)
            if event.activate_target:
                bar_id = _make_activation_bar(
                    root, next_id, p_cells, participants,
                    event.target, current_y, MESSAGE_STEP,
                )
                active_bars[event.target] = bar_id
                target_cell = bar_id

            if event.deactivate_source:
                bar_cell = active_bars.pop(event.source, None)
                if bar_cell is not None:
                    # Stretch the activation bar to current_y
                    source_cell = bar_cell
                else:
                    source_cell = p_cells[event.source]

            # Arrow style: compute exit/entry based on direction
            label = _escape_xml(event.label)
            if src_idx < tgt_idx:
                exit_x, exit_y = "1", "0.5"
                entry_x, entry_y = "0", "0.5"
            elif src_idx > tgt_idx:
                exit_x, exit_y = "0", "0.5"
                entry_x, entry_y = "1", "0.5"
            else:  # self-message
                exit_x, exit_y = "1", "0.5"
                entry_x, entry_y = "1", "0.75"

            style_parts = [
                "html=1", "rounded=0",
                f"exitX={exit_x};exitY={exit_y}",
                f"entryX={entry_x};entryY={entry_y}",
                "endArrow=block",
            ]
            if event.dashed:
                style_parts.append("dashed=1")
            style = ";".join(style_parts)

            edge_id = next_id()
            edge = ET.SubElement(
                root, "mxCell",
                id=edge_id,
                value=label,
                style=style,
                edge="1", parent="1",
                source=source_cell, target=target_cell,
            )
            # Add a geometry with a manual offset to position the label and arrow
            geo = ET.SubElement(edge, "mxGeometry", relative="1", as_="geometry")
            # For self-messages, add an array of points
            if src_idx == tgt_idx:
                ET.SubElement(geo, "Array", as_="points")

            current_y += MESSAGE_STEP

        elif isinstance(event, Activate):
            bar_id = _make_activation_bar(
                root, next_id, p_cells, participants,
                event.target, current_y, MESSAGE_STEP,
            )
            active_bars[event.target] = bar_id

        elif isinstance(event, Deactivate):
            bar_cell = active_bars.pop(event.target, None)
            if bar_cell is not None:
                # Find and update the activation bar's height to current_y - bar_start_y
                _update_bar_height(root, bar_cell, current_y)

        elif isinstance(event, Note):
            _make_note(root, next_id, p_cells, participants, event, current_y)
            current_y += MESSAGE_STEP

        elif isinstance(event, Fragment):
            if event.kind == "end":
                if fragment_stack:
                    f = fragment_stack.pop()
                    _close_fragment(root, next_id, p_cells, participants, f,
                                    HEADER_Y, current_y, PARTICIPANT_W,
                                    PARTICIPANT_GAP, START_X)
            else:
                fragment_stack.append({
                    "kind": event.kind,
                    "condition": event.condition,
                    "start_y": current_y,
                    "cell_id": None,
                })

    # Close any unclosed fragments
    for f in reversed(fragment_stack):
        _close_fragment(root, next_id, p_cells, participants, f,
                        HEADER_Y, current_y, PARTICIPANT_W,
                        PARTICIPANT_GAP, START_X)

    # ── Pretty-print XML ──
    rough = ET.tostring(mxfile, encoding="unicode")
    dom = minidom.parseString(rough)
    xml_str = dom.toprettyxml(indent="  ", encoding=None)

    # minidom adds <?xml...?> line; strip it for clean drawio output
    lines = xml_str.splitlines()
    if lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines)


def _make_activation_bar(
    root: ET.Element, next_id, p_cells, participants,
    target: str, y: int, height: int,
) -> str:
    """Create an activation bar on a lifeline. Returns the cell id."""
    idx = _participant_index(participants, target)
    bar_id = next_id()
    parent_id = p_cells[target]

    # Activation bar: centered in lifeline (lifeline W=80, bar W=24 → x=28)
    style = (
        "shape=umlActivation;"
        "whiteSpace=wrap;html=1;"
        "backgroundOutline=1;"
        f"fillColor={ACTIVATION_FILL};"
        "gradientColor=none;"
        "rounded=0;"
    )
    ET.SubElement(
        root, "mxCell",
        id=bar_id,
        value="",
        style=style,
        vertex="1", parent=parent_id,
        connectable="0",
    ).append(
        ET.Element("mxGeometry",
                   x="28", y=str(y - HEADER_Y),
                   width=str(ACTIVATION_W), height=str(height),
                   as_="geometry")
    )
    return bar_id


def _update_bar_height(root: ET.Element, bar_cell_id: str, current_y: int):
    """Update an activation bar's height to cover up to current_y."""
    # Find the mxCell with the given id and update its mxGeometry
    for cell in root.iter("mxCell"):
        if cell.get("id") == bar_cell_id:
            geo = cell.find("mxGeometry")
            if geo is not None:
                old_y = float(geo.get("y", "0"))
                geo.set("height", str(int(current_y - old_y)))
            break


def _make_note(
    root: ET.Element, next_id, p_cells, participants,
    note: Note, y: int,
):
    """Create a note shape."""
    if note.position == "over":
        targets = note.targets
        if len(targets) >= 2:
            first = _participant_index(participants, targets[0])
            last = _participant_index(participants, targets[-1])
            w = (last - first) * PARTICIPANT_GAP + PARTICIPANT_W
            x = START_X + first * PARTICIPANT_GAP
        else:
            idx = _participant_index(participants, targets[0])
            w = NOTE_W
            x = START_X + idx * PARTICIPANT_GAP + (PARTICIPANT_W - w) // 2
    elif note.position == "left of":
        idx = _participant_index(participants, note.targets[0])
        w = NOTE_W
        x = START_X + idx * PARTICIPANT_GAP - w - 20
    else:  # right of
        idx = _participant_index(participants, note.targets[0])
        w = NOTE_W
        x = START_X + idx * PARTICIPANT_GAP + PARTICIPANT_W + 20

    style = (
        "shape=note;whiteSpace=wrap;html=1;"
        "fillColor=#FFF9C4;strokeColor=#F9A825;"
        "rounded=0;fontSize=11;"
    )
    nid = next_id()
    ET.SubElement(
        root, "mxCell",
        id=nid,
        value=_escape_xml(note.text),
        style=style,
        vertex="1", parent="1",
    ).append(
        ET.Element("mxGeometry",
                   x=str(x), y=str(y),
                   width=str(w), height=str(NOTE_H),
                   as_="geometry")
    )


def _close_fragment(
    root: ET.Element, next_id, p_cells, participants,
    frag: dict, header_y: int, current_y: int,
    participant_w: int, participant_gap: int, start_x: int,
):
    """Draw a frame rectangle for loop/alt/opt."""
    if not participants:
        return

    first_x = start_x
    last_idx = len(participants) - 1
    last_x = start_x + last_idx * participant_gap + participant_w
    frame_w = last_x - first_x
    frame_h = current_y - frag["start_y"] + MESSAGE_STEP

    if frame_h < 60:
        frame_h = 60

    color_map = {
        "loop": LOOP_COLOR,
        "alt": ALT_COLOR,
        "else": ALT_COLOR,
        "opt": OPT_COLOR,
        "rect": RECT_COLOR,
    }
    border_map = {
        "loop": "#388E3C",
        "alt": "#E65100",
        "else": "#E65100",
        "opt": "#1565C0",
        "rect": "#6A1B9A",
    }
    fill = color_map.get(frag["kind"], "#F5F5F5")
    border = border_map.get(frag["kind"], "#666666")

    label = f"<b>{frag['kind'].upper()}</b>"
    if frag["condition"]:
        label += f": {_escape_xml(frag['condition'])}"

    nid = next_id()

    style = (
        "shape=umlFrame;"
        "whiteSpace=wrap;html=1;"
        f"fillColor={fill};"
        f"strokeColor={border};"
        "strokeWidth=2;"
        "rounded=0;fontSize=11;"
        "verticalAlign=top;align=left;"
        "spacingTop=2;spacingLeft=4;"
    )
    ET.SubElement(
        root, "mxCell",
        id=nid,
        value=label,
        style=style,
        vertex="1", parent="1",
    ).append(
        ET.Element("mxGeometry",
                   x=str(first_x), y=str(frag["start_y"]),
                   width=str(frame_w), height=str(frame_h),
                   as_="geometry")
    )


def _escape_xml(text: str) -> str:
    """Escape text for XML attribute/content."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert Mermaid sequence diagram to Draw.io format.",
    )
    parser.add_argument(
        "input", nargs="?",
        help="Input file (.mmd, .md, or .txt). Reads from stdin if omitted.",
    )
    parser.add_argument("-o", "--output", help="Output .drawio file.")
    parser.add_argument(
        "--svg", action="store_true",
        help="Also export to SVG via draw.io CLI (requires drawio in PATH).",
    )
    args = parser.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            mermaid_text = f.read()
    else:
        mermaid_text = sys.stdin.read()

    participants, events = parse_mermaid(mermaid_text)

    if not participants:
        print("error: no participants found in Mermaid diagram", file=sys.stderr)
        sys.exit(1)

    xml_str = generate_drawio_xml(participants, events)

    output_path = args.output or (
        args.input.rsplit(".", 1)[0] + ".drawio" if args.input else "output.drawio"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    msg = (
        f"✓ Converted {len(participants)} participants, "
        f"{sum(1 for e in events if isinstance(e, Message))} messages"
    )
    print(msg, file=sys.stderr)
    print(f"  → {output_path}", file=sys.stderr)

    if args.svg:
        svg_path = output_path.rsplit(".", 1)[0] + ".svg"
        try:
            subprocess.run(
                ["drawio", "--export", "--format", "svg",
                 "--output", svg_path, output_path],
                check=True, capture_output=True, text=True, timeout=30,
            )
            print(f"  → {svg_path} (SVG)", file=sys.stderr)
        except FileNotFoundError:
            print(
                "error: drawio CLI not found; install with: brew install --cask drawio",
                file=sys.stderr,
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"error: drawio export failed: {e.stderr.strip() or e}",
                  file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
