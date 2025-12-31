---
title: "Multi-Player Trading Game MVP Implementation"
description: "Real-time cooperative trading game with MT5 demo accounts, leaderboards, and team competition"
status: in-progress
priority: P1
effort: 105h
issue: null
branch: feat/multi-player-feature-with-dashboard
tags: [multiplayer, mt5, realtime, backend, database, websocket]
created: 2025-12-31
last_updated: 2025-12-31
phase_01_completed: 2025-12-31
---

# Multi-Player Trading Game MVP Implementation Plan

## Overview

Transform EV GamePad into cooperative multi-player trading game where 5-10 friends compete in teams via chat commands with real-time leaderboards and authentic MT5 demo account execution.

**Scope:** Sprints 1-3 (MVP - Core Multiplayer Functionality)
**Total Effort:** 105 hours (5 weeks)
**Target Scale:** 5-10 concurrent players

## Key Features

1. **Real-Time Leaderboard** - Sub-50ms updates via Redis sorted sets, `/top` command
2. **MT5 Integration** - Real broker execution with account pool management
3. **Team Competition** - `/csv` and `/jsv` commands for game sessions
4. **WebSocket Real-Time** - Socket.IO room-based updates
5. **Account Pool** - Pre-provisioned 10 demo accounts with allocation logic

## Architecture Summary

```
FastAPI + Socket.IO Backend
├── Leaderboard Service (Redis sorted sets, materialized views)
├── MT5 Integration Service (account pool, order routing, position sync)
├── Game Service (session lifecycle, team formation)
├── Team Scoring Service (P&L aggregation)
└── Command Parser (/csv, /jsv, /top)

Database Layer
├── PostgreSQL (sessions, teams, mt5_accounts, orders, positions)
└── Redis (leaderboard cache, account allocation, session state)

External Integration
└── MT5 Terminal (MetaTrader5 Python library)
```

## Phases

| # | Phase | Status | Effort | Link |
|---|-------|--------|--------|------|
| 1 | Leaderboard Infrastructure | Done | 40h | [phase-01](./phase-01-leaderboard-infrastructure.md) |
| 2 | MT5 Integration Service | Pending | 35h | [phase-02-mt5-integration-service.md) |
| 3 | Game Sessions & Teams | Pending | 30h | [phase-03-game-sessions-teams.md) |

## Dependencies

### Infrastructure
- PostgreSQL database (existing)
- Redis server (existing)
- MT5 terminal with 10 pre-provisioned demo accounts
- FastAPI + Socket.IO server (existing)

### Python Libraries
- `MetaTrader5` - MT5 Python API
- `python-socketio` - WebSocket server (existing)
- `asyncpg` - PostgreSQL async driver
- `redis-py` - Redis client (existing)

### External Services
- MT5 broker demo accounts (manual provisioning required)

## Critical Success Factors

### Performance
- [ ] Leaderboard update < 50ms (Redis Tier 1)
- [ ] MT5 order execution < 500ms
- [ ] `/top` command response < 200ms
- [ ] Position sync < 5 seconds
- [ ] Support 5-10 concurrent players

### MT5 Integration
- [ ] All 10 demo accounts login successfully
- [ ] Order execution returns valid MT5 tickets
- [ ] Position sync accurate (MT5 ↔ DB)
- [ ] Account allocation/release without leaks
- [ ] Health check detects disconnect within 10s

### Multiplayer Functionality
- [ ] `/csv` creates new game sessions
- [ ] `/jsv` joins existing sessions
- [ ] `/top` shows real-time rankings
- [ ] Team P&L aggregation accurate
- [ ] Real-time updates via Socket.IO

## Risk Assessment

### HIGH Risks
1. **MT5 Terminal Downtime** - All gameplay stops, no fallback (mitigation: health monitoring, pause sessions)
2. **Account Pool Exhaustion** - Player #11 blocked (mitigation: reserve 2 spare accounts, alerts)
3. **Demo Account Expiry** - Mid-session disconnect (mitigation: weekly monitoring, 14-day renewal buffer)

### MEDIUM Risks
1. **WebSocket Connection Stability** - Real-time updates fail (mitigation: auto-reconnect, exponential backoff)
2. **Leaderboard Consistency** - Race conditions (mitigation: 3-tier caching, Redis atomic operations)
3. **Position Sync Lag** - Delayed P&L updates (mitigation: 5s polling, optimistic updates)

## Security Considerations

- **MT5 Credentials** - Store encrypted in database, never expose to frontend
- **Session Isolation** - Each game session isolated by session_id
- **Account Pool Access** - Row-level locking for allocation
- **Input Validation** - Sanitize all chat commands
- **Rate Limiting** - Prevent command spam

## Operational Requirements

### Pre-Launch Checklist
- [ ] Provision 10 MT5 demo accounts
- [ ] Record credentials in encrypted vault
- [ ] Populate `mt5_account_pool` table
- [ ] Verify MT5 terminal connectivity
- [ ] Test account allocation/release cycle
- [ ] Setup expiry monitoring alerts

### Weekly Maintenance (30 min)
- [ ] Check account expiry dates (14-day buffer)
- [ ] Verify MT5 login for all accounts
- [ ] Monitor available account count
- [ ] Review broker policy changes

## Next Steps

1. **Review brainstorm document** - `/plans/reports/brainstorm-251230-2302-multiplayer-trading-game.md`
2. **Start Phase 1** - Leaderboard infrastructure implementation
3. **Provision MT5 accounts** - Before Phase 2 (parallel task)
4. **Setup monitoring** - Health checks, alerts, dashboards

## Resolved Decisions

1. ✅ **MT5 Broker** - Fixed broker selected for demo accounts
2. ✅ **Health Check Interval** - 10s confirmed optimal
3. ✅ **Session Close** - Owner manually closes session (no auto-complete)
4. ✅ **Team Naming** - Team name = Server name (not auto Team A/B)
5. ✅ **Position Management** - Keep positions open on player leave

## Unresolved Questions

1. **Achievement System** - Include in MVP or defer to Phase 4?
2. **Frontend Dashboard** - React component or CLI-only for MVP?
3. **Testing Strategy** - Real MT5 accounts or mock for integration tests?
