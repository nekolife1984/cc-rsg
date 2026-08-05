#!/usr/bin/env python3
"""Tests for mermaid2drawio.py"""

import sys
import os
import xml.etree.ElementTree as ET

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mermaid2drawio import parse_mermaid, generate_drawio_xml, Participant, Message, Fragment, Note, Activate, Deactivate


# ── Parser Tests ──────────────────────────────────────────────────────────────

def test_parse_participants():
    """Basic participant declarations."""
    text = """sequenceDiagram
    participant A
    participant Bob as B-chan
    actor Alice
"""
    participants, events = parse_mermaid(text)
    assert len(participants) == 3, f"expected 3, got {len(participants)}"
    pnames = {p.id for p in participants}
    assert "A" in pnames
    assert "Bob" in pnames
    # Bob has label "B-chan"
    bob = next(p for p in participants if p.id == "Bob")
    assert bob.label == "B-chan", f"expected B-chan, got {bob.label}"
    alice = next(p for p in participants if p.id == "Alice")
    assert alice.actor, "Alice should be an actor"


def test_parse_messages():
    """Solid and dashed messages."""
    text = """sequenceDiagram
    participant A
    participant B
    A->>B: Hello
    B-->>A: World
"""
    participants, events = parse_mermaid(text)
    assert len(events) == 2
    assert isinstance(events[0], Message)
    assert events[0].source == "A"
    assert events[0].target == "B"
    assert events[0].label == "Hello"
    assert not events[0].dashed
    assert isinstance(events[1], Message)
    assert events[1].source == "B"
    assert events[1].target == "A"
    assert events[1].label == "World"
    assert events[1].dashed


def test_parse_activation_shortcut():
    """Activation markers on arrows: +B / -A."""
    text = """sequenceDiagram
    participant A
    participant B
    A->>+B: activate target
    B-->>-A: deactivate source
"""
    participants, events = parse_mermaid(text)
    assert len(events) == 2
    assert events[0].activate_target
    assert not events[0].deactivate_source
    assert events[1].deactivate_source
    assert not events[1].activate_target


def test_parse_activate_deactivate():
    """Explicit activate / deactivate lines."""
    text = """sequenceDiagram
    participant A
    participant B
    A->>B: msg
    activate B
    B->>A: processing
    deactivate B
"""
    participants, events = parse_mermaid(text)
    assert len(events) == 4
    assert isinstance(events[0], Message)
    assert isinstance(events[1], Activate)
    assert events[1].target == "B"
    assert isinstance(events[2], Message)
    assert isinstance(events[3], Deactivate)
    assert events[3].target == "B"


def test_parse_notes():
    """Note over, left of, right of."""
    text = """sequenceDiagram
    participant A
    participant B
    Note over A,B: group note
    Note left of A: left note
    Note right of B: right note
"""
    participants, events = parse_mermaid(text)
    notes = [e for e in events if isinstance(e, Note)]
    assert len(notes) == 3
    assert notes[0].position == "over"
    assert notes[0].targets == ["A", "B"]
    assert notes[0].text == "group note"
    assert notes[1].position == "left of"
    assert notes[2].position == "right of"


def test_parse_fragments():
    """Loop / alt / opt fragments."""
    text = """sequenceDiagram
    participant A
    participant B
    loop Every second
        A->>B: ping
        B-->>A: pong
    end
    alt Success
        A->>B: done
    else Failure
        A->>B: retry
    end
"""
    participants, events = parse_mermaid(text)
    assert len(events) == 9
    assert isinstance(events[0], Fragment) and events[0].kind == "loop"
    assert events[0].condition == "Every second"
    assert isinstance(events[3], Fragment) and events[3].kind == "end"
    assert isinstance(events[4], Fragment) and events[4].kind == "alt"
    assert events[4].condition == "Success"
    assert isinstance(events[6], Fragment) and events[6].kind == "else"
    assert events[6].condition == "Failure"
    assert isinstance(events[8], Fragment) and events[8].kind == "end"


def test_parse_autonumber():
    """autonumber line is ignored."""
    text = """sequenceDiagram
    autonumber
    participant A
    participant B
    A->>B: msg
"""
    participants, events = parse_mermaid(text)
    assert len(events) == 1
    assert isinstance(events[0], Message)


def test_parse_auto_register():
    """Participants used in messages but not declared are auto-registered."""
    text = """sequenceDiagram
    A->>B: hello
"""
    participants, events = parse_mermaid(text)
    assert len(participants) == 2
    pids = {p.id for p in participants}
    assert "A" in pids
    assert "B" in pids


# ── Draw.io XML Tests ────────────────────────────────────────────────────────

def test_generate_xml_has_lifelines():
    """Generated XML contains lifeline cells for each participant."""
    participants = [Participant("A"), Participant("B")]
    events = [Message("A", "B", "hello")]
    xml_str = generate_drawio_xml(participants, events)
    root = ET.fromstring(xml_str)
    cells = root.findall(".//mxCell")
    # Should have root cells (0,1) + 2 lifelines + 1 arrow + 1 activation?
    # A->>B creates a message with no activation markers, so just 2 lifelines + 1 edge
    lifelines = [c for c in cells if c.get("style", "").startswith("shape=umlLifeline")]
    assert len(lifelines) == 2, f"expected 2 lifelines, got {len(lifelines)}"
    values = {l.get("value") for l in lifelines}
    assert "A" in values
    assert "B" in values


def test_generate_xml_has_message():
    """Generated XML contains edge for a message."""
    participants = [Participant("A"), Participant("B")]
    events = [Message("A", "B", "hello")]
    xml_str = generate_drawio_xml(participants, events)
    root = ET.fromstring(xml_str)
    edges = [c for c in root.findall(".//mxCell") if c.get("edge") == "1"]
    assert len(edges) == 1
    assert edges[0].get("value") == "hello"


def test_generate_xml_has_activation():
    """Generated XML contains activation bar when activate/deactivate used."""
    participants = [Participant("A"), Participant("B")]
    events = [
        Message("A", "B", "request", activate_target=True),
        Message("B", "A", "response", deactivate_source=True),
    ]
    xml_str = generate_drawio_xml(participants, events)
    root = ET.fromstring(xml_str)
    activations = [c for c in root.findall(".//mxCell") if "umlActivation" in (c.get("style") or "")]
    assert len(activations) >= 1


def test_generate_xml_has_note():
    """Generated XML contains note shape."""
    participants = [Participant("A")]
    events = [Note("over", ["A"], "hello note")]
    xml_str = generate_drawio_xml(participants, events)
    root = ET.fromstring(xml_str)
    notes = [c for c in root.findall(".//mxCell") if "shape=note" in (c.get("style") or "")]
    assert len(notes) == 1
    assert "hello note" in notes[0].get("value", "")


def test_generate_xml_has_frame():
    """Generated XML contains frame for loop."""
    participants = [Participant("A"), Participant("B")]
    events = [
        Fragment("loop", "Every second"),
        Message("A", "B", "ping"),
        Fragment("end"),
    ]
    xml_str = generate_drawio_xml(participants, events)
    root = ET.fromstring(xml_str)
    frames = [c for c in root.findall(".//mxCell") if "umlFrame" in (c.get("style") or "")]
    assert len(frames) == 1
    assert "LOOP" in frames[0].get("value", "")


def test_empty_diagram_no_crash():
    """Empty or minimal input doesn't crash."""
    xml_str = generate_drawio_xml([Participant("A")], [])
    root = ET.fromstring(xml_str)
    cells = root.findall(".//mxCell")
    assert any("umlLifeline" in (c.get("style") or "") for c in cells)
