# FRONTEND CODEBASE ANALYSIS - EV GamePad

## SUMMARY
- 99 TypeScript/TSX files (~22,900 LOC)
- 80 React components (~18,658 LOC)
- 6 custom hooks, 4 pages, 1 context provider
- Socket.IO WebSocket architecture
- Gamepad controller support (Xbox Standard API)
- Multi-monitor trading dashboard with AI advisor

## PAGES (4 routing targets)
1. Portfolio (/) - Monitor 1: Risk management, position input, active orders
2. Plan (/plan) - Monitor 2: Market analysis, KOL feeds, AI analysis
3. Action (/action) - Monitor 3: Advisor interface
4. NotFound (*) - 404 error page

## CUSTOM HOOKS (6)
- useTrading.ts (367 LOC) - MT5 trading ops: login, buy, sell, modify, close
- useAdvisor.ts (443 LOC) - AI analysis: technical, multi-TF, patterns, risk, recommendations
- usePortfolioAnalysis.ts (156 LOC) - Portfolio risk assessment
- useGamepad.ts (120 LOC) - Xbox controller polling and mapping
- useAccuracyTracking.ts - Track recommendation accuracy (partial)
- use-toast.ts - Toast notifications

## SOCKET.IO EVENTS
Trading: login→login_result, buy/sell→order_result, modify→modify_result, close→close_result
Advisor: advisor_technical_summary→technical_result, advisor_recommendation→recommendation_result (with chain-of-thought)
Market: kol:new_message (real-time trader signals)
Connection: connected, disconnect, reconnect_attempt, etc.

## COMPONENTS BY CATEGORY
Trading (6): OrderEntry, PositionManager, ActiveOrders, RiskManagement, PositionInputForm, AIRiskAdvisory
Market (6): MarketOverview, MarketSentiment, PriceAction, AIAnalysis, KOLUpdatesFeed, MajorNews
Advisor (4): ChainOfThoughtViewer, AccuracyMetrics, IndicatorOverlay, ProvenanceTimeline
Chat Cards (3): TechnicalAnalysis, RiskAnalysis, PatternAnalysis
System (8): GlobalGamepad, GamepadHints, GamepadPositions, GamepadQuickTrade, SystemHeader, MonitorNav, MissionLog, CapitalCompanion
UI Primitives (42): Radix UI + shadcn/ui wrappers
Examples (2): TradingExample, AdvisorExample
KOL (2): KOLUpdatesFeed, KOLUpdatesPanel

## KEY TYPES
KOLMessage, AccountInfo, OrderRequest/Result, Position, PortfolioAnalysisResult
TechnicalSummaryResult, MultiTimeframeResult, PatternScanResult, RiskAnalysisResult
RecommendationResult (with explainability: steps, scores, risks, data gaps)

## STYLING
Tailwind CSS + Radix UI + shadcn/ui
Custom: .scanlines, .crt-flicker, .panel, .terminal-green, .danger-red

## DEPENDENCIES
react@18.3.1, typescript@5.9.3, vite@5.4.21
socket.io-client@4.8.1
react-hook-form@7.69.0, zod@3.25.76
react-router-dom@6.30.2
@radix-ui/* (27 packages), tailwindcss@3.4.19
recharts@2.15.4, lucide-react@0.462.0
@tanstack/react-query@5.90.12, sonner@1.7.4

## ARCHITECTURE PATTERNS
- Promise-wrapped Socket events (socket.once + cleanup)
- Multi-timeframe analysis with alignment detection
- Gamepad navigation via global event dispatch
- Component-level error handling + ErrorBoundary
- Modular UI/logic/data separation

## KEY FILES
Context: src/context/SocketContext.tsx (126 LOC)
Hooks: src/hooks/{useTrading,useAdvisor,usePortfolioAnalysis,useGamepad}.ts
Pages: src/pages/{Portfolio,Plan,Action,NotFound}.tsx
Components: src/components/{*Panel,*Card,Gamepad*,System*}.tsx (80 files)
Types: src/types/{index,kol}.ts
Main: src/App.tsx

## OBSERVATIONS
Strengths: Clean Socket.IO patterns, full TypeScript, modular components, gamepad support, AI explainability, real-time KOL, multi-TF analysis
Concerns: Some demo data (AIAnalysis, MarketOverview), useAccuracyTracking partial, no visible tests, order recovery strategy unclear
