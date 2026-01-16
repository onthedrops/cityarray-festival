# CITYARRAY Project Context Prompt

**Paste this at the start of any new Claude chat to get immediately productive.**

---

## Who I Am

I'm Eben, a 27-year radio/media professional turned technology entrepreneur. I'm building CITYARRAY, an AI-powered emergency communications platform.

## What CITYARRAY Is

Two independent product tracks:

### Festival Edition (Raspberry Pi Platform)
- **Hardware**: Pi 5 + Hailo-8L (13 TOPS) + AI camera + mic/speaker
- **Software**: `demo_full.py` runs the system with Ollama, YOLOv8, TTS in 5 languages
- **Status**: WORKING PROTOTYPE ASSEMBLED
- **Use case**: Portable signage for festivals, events, concerts
- **Business model**: Rental ($150-250/day) + Sales ($3,500-5,500/unit)

### City Edition (NVIDIA Jetson Platform)  
- **Hardware**: Jetson Orin Nano Super (67 TOPS) + outdoor LED + sensors + two-way audio
- **Software**: VLM (Moondream 2B) for scene understanding + message generation
- **Status**: Planning/documentation phase
- **Use case**: Permanent municipal emergency communications infrastructure
- **Business model**: Municipal sales ($25,000-55,000/unit) + acquisition target (Motorola/Axon)

## Key Technical Decisions

- Festival uses **Hailo-8L for CNN** (YOLOv8 crowd detection) — cannot run VLMs
- City uses **Jetson Orin for VLM** (Moondream 2B in 2-4 seconds)
- Both have **two-way audio**: speaker for TTS announcements, microphone for crowd noise estimation
- Festival mic is for crowd noise only; City mic also supports accessibility/community input

## GitHub Repositories

- `onthedrops/cityarray-festival` — Festival Edition issues/project board
- `onthedrops/cityarray-city` — City Edition issues/project board  
- `onthedrops/cityarray-sdk` — Working code (demo_full.py, etc.)
- `onthedrops/trends-report-system` — Separate project (trends analysis platform)

## GitHub Projects (Visual Task Tracking)

- Festival Edition: https://github.com/users/onthedrops/projects/2
- City Edition: https://github.com/users/onthedrops/projects/3

## What's Already Built (Festival)

| Component | Status | Notes |
|-----------|--------|-------|
| Pi 5 + Hailo-8L hardware | ✅ Assembled | With mic, speaker, AI camera |
| demo_full.py | ✅ Working | Main controller script |
| YOLOv8 crowd detection | ✅ Working | Runs on Hailo |
| Ollama integration | ✅ Working | Local LLM |
| TTS in 5 languages | ✅ Working | Audio announcements |
| Display manager | ✅ Working | E-paper/LED control |
| Emergency mode | ✅ Working | Override + audio alerts |

## What's Needed (Festival Sprint)

| Task | Priority | GitHub Issue |
|------|----------|--------------|
| Pre-built message templates | High | In project board |
| Event control dashboard (web) | High | Upgrade from demo_control.html |
| Offline operation mode | High | Queue when connectivity fails |
| Fleet management | Medium | Multi-unit battery/status |
| Sponsor content integration | Low | Scheduled rotation + CPM tracking |

## Documentation Files

These exist in the repos or were created in Claude chats:
- `cityarray-dual-track-analysis.md` — Full Festival vs City comparison
- `cityarray-led-sign-specifications.md` — Hardware BOM and costs
- `edge-ai-jetson-vs-pi-analysis.md` — Red team analysis of compute platforms

## Business Context

- **Target exit**: Acquisition by Motorola Solutions, Axon, or PE (6-12 month horizon for City Edition)
- **Thought leadership**: "Maternal AI" positioning — AI that protects/nurtures communities vs. agentic AI
- **Grant opportunities**: NSF SBIR, FEMA preparedness grants, state homeland security

## How to Help Me

1. **Check GitHub first** — Issues and project boards have current sprint tasks
2. **Reference existing code** — demo_full.py and cityarray-sdk have working implementations
3. **Don't re-explain basics** — I know the tech stack, just help me build
4. **Be direct** — Give me code, commands, and files, not long explanations

## Current Focus

[UPDATE THIS SECTION EACH CHAT]

Today I'm working on: _____________________

Specific task: _____________________

---

**End of context. Now help me with:**
