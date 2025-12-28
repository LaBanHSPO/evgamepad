# Skills Catalog

Auto-generated catalog of all available skills in ClaudeKit Engineer.

**Last Updated**: 2025-11-21

**Total Skills**: 33

## Categories

- [AI & Machine Learning](#ai-ml)
- [Backend Development](#backend)
- [Database & Storage](#database)
- [Development Tools](#dev-tools)
- [Frameworks & Platforms](#frameworks)
- [Frontend & Design](#frontend)
- [Infrastructure & DevOps](#infrastructure)
- [Multimedia & Processing](#multimedia)
- [Utilities & Helpers](#utilities)

## Legend

- 📦 Has executable scripts
- 📚 Has reference documentation

## AI & Machine Learning

### 📦 📚 `ai-multimodal`

Process and generate multimedia content using Google Gemini API. Capabilities include analyze audio files (transcription with timestamps, summarization, speech understanding, music/sound analysis up to 9.5 hours), understand images (captioning, object detection, OCR, visual Q&A, segmentation), process videos (scene detection, Q&A, temporal analysis, YouTube URLs, up to 6 hours), extract from documents (PDF tables, forms, charts, diagrams, multi-page), generate images (text-to-image with Imagen 4, editing, composition, refinement), generate videos (text-to-video with Veo 3, 8-second clips with native audio). Use when working with audio/video files, analyzing images or screenshots, processing PDF documents, extracting structured data from media, creating images/videos from text prompts, or implementing multimodal AI features. Supports Gemini 3/2.5, Imagen 4, and Veo 3 models with context windows up to 2M tokens.

**Location**: `.claude/skills/ai-multimodal/SKILL.md`

### `google-adk-python`

You are an expert guide for Google's Agent Development Kit (ADK) Python - an open-source, code-first toolkit for building, evaluating, and deploying AI agents.

**Location**: `.claude/skills/google-adk-python/SKILL.md`

## Backend Development

### 📚 `backend-development`

Build robust backend systems with modern technologies (Node.js, Python, Go, Rust), frameworks (NestJS, FastAPI, Django), databases (PostgreSQL, MongoDB, Redis), APIs (REST, GraphQL, gRPC), authentication (OAuth 2.1, JWT), testing strategies, security best practices (OWASP Top 10), performance optimization, scalability patterns (microservices, caching, sharding), DevOps practices (Docker, Kubernetes, CI/CD), and monitoring. Use when designing APIs, implementing authentication, optimizing database queries, setting up CI/CD pipelines, handling security vulnerabilities, building microservices, or developing production-ready backend systems.

**Location**: `.claude/skills/backend-development/SKILL.md`

### 📦 📚 `better-auth`

Implement authentication and authorization with Better Auth - a framework-agnostic TypeScript authentication framework. Features include email/password authentication with verification, OAuth providers (Google, GitHub, Discord, etc.), two-factor authentication (TOTP, SMS), passkeys/WebAuthn support, session management, role-based access control (RBAC), rate limiting, and database adapters. Use when adding authentication to applications, implementing OAuth flows, setting up 2FA/MFA, managing user sessions, configuring authorization rules, or building secure authentication systems for web applications.

**Location**: `.claude/skills/better-auth/SKILL.md`

### 📦 📚 `payment-integration`

Implement payment integrations with SePay (Vietnamese payment gateway with VietQR, bank transfers, cards) and Polar (global SaaS monetization platform with subscriptions, usage-based billing, automated benefits). Use when integrating payment processing, implementing checkout flows, managing subscriptions, handling webhooks, processing bank transfers, generating QR codes, automating benefit delivery, or building billing systems. Supports authentication (API keys, OAuth2), product management, customer portals, tax compliance (Polar as MoR), and comprehensive SDK integrations (Node.js, PHP, Python, Go, Laravel, Next.js).

**Location**: `.claude/skills/payment-integration/SKILL.md`

## Database & Storage

### 📦 📚 `databases`

Work with MongoDB (document database, BSON documents, aggregation pipelines, Atlas cloud) and PostgreSQL (relational database, SQL queries, psql CLI, pgAdmin). Use when designing database schemas, writing queries and aggregations, optimizing indexes for performance, performing database migrations, configuring replication and sharding, implementing backup and restore strategies, managing database users and permissions, analyzing query performance, or administering production databases.

**Location**: `.claude/skills/databases/SKILL.md`

## Development Tools

### 📚 `claude-code`

Activate when users ask about Claude Code installation, slash commands (/cook, /plan, /fix, /test, /docs, /design, /git), creating/managing Agent Skills, configuring MCP servers, setting up hooks/plugins, IDE integration (VS Code, JetBrains), CI/CD workflows, enterprise deployment (SSO, RBAC, sandboxing), troubleshooting authentication/performance issues, or advanced features (extended thinking, caching, checkpointing).

**Location**: `.claude/skills/claude-code/SKILL.md`

### 📦 📚 `docs-seeker`

Search technical documentation using executable scripts to detect query type, fetch from llms.txt sources (context7.com), and analyze results. Use when user needs: (1) Topic-specific documentation (features/components/concepts), (2) Library/framework documentation, (3) GitHub repository analysis, (4) Documentation discovery with automated agent distribution strategy

**Location**: `.claude/skills/docs-seeker/SKILL.md`

### 📦 📚 `mcp-management`

Manage Model Context Protocol (MCP) servers - discover, analyze, and execute tools/prompts/resources from configured MCP servers. Use when working with MCP integrations, need to discover available MCP capabilities, filter MCP tools for specific tasks, execute MCP tools programmatically, access MCP prompts/resources, or implement MCP client functionality. Supports intelligent tool selection, multi-server management, and context-efficient capability discovery.

**Location**: `.claude/skills/mcp-management/SKILL.md`

### 📦 📚 `repomix`

Package entire code repositories into single AI-friendly files using Repomix. Capabilities include pack codebases with customizable include/exclude patterns, generate multiple output formats (XML, Markdown, plain text), preserve file structure and context, optimize for AI consumption with token counting, filter by file types and directories, add custom headers and summaries. Use when packaging codebases for AI analysis, creating repository snapshots for LLM context, analyzing third-party libraries, preparing for security audits, generating documentation context, or evaluating unfamiliar codebases.

**Location**: `.claude/skills/repomix/SKILL.md`

### 📦 `skill-creator`

Guide for creating effective skills, adding skill references, skill scripts or optimizing existing skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, frameworks, libraries or plugins usage, or API and tool integrations.

**Location**: `.claude/skills/skill-creator/SKILL.md`

## Frameworks & Platforms

### 📚 `mobile-development`

Build modern mobile applications with React Native, Flutter, Swift/SwiftUI, and Kotlin/Jetpack Compose. Covers mobile-first design principles, performance optimization (battery, memory, network), offline-first architecture, platform-specific guidelines (iOS HIG, Material Design), testing strategies, security best practices, accessibility, app store deployment, and mobile development mindset. Use when building mobile apps, implementing mobile UX patterns, optimizing for mobile constraints, or making native vs cross-platform decisions.

**Location**: `.claude/skills/mobile-development/SKILL.md`

### 📦 📚 `shopify`

Build Shopify applications, extensions, and themes using GraphQL/REST APIs, Shopify CLI, Polaris UI components, and Liquid templating. Capabilities include app development with OAuth authentication, checkout UI extensions for customizing checkout flow, admin UI extensions for dashboard integration, POS extensions for retail, theme development with Liquid, webhook management, billing API integration, product/order/customer management. Use when building Shopify apps, implementing checkout customizations, creating admin interfaces, developing themes, integrating payment processing, managing store data via APIs, or extending Shopify functionality.

**Location**: `.claude/skills/shopify/SKILL.md`

### 📦 📚 `web-frameworks`

Build modern full-stack web applications with Next.js (App Router, Server Components, RSC, PPR, SSR, SSG, ISR), Turborepo (monorepo management, task pipelines, remote caching, parallel execution), and RemixIcon (3100+ SVG icons in outlined/filled styles). Use when creating React applications, implementing server-side rendering, setting up monorepos with multiple packages, optimizing build performance and caching strategies, adding icon libraries, managing shared dependencies, or working with TypeScript full-stack projects.

**Location**: `.claude/skills/web-frameworks/SKILL.md`

## Frontend & Design

### 📚 `aesthetic`

Create aesthetically beautiful interfaces following proven design principles. Use when building UI/UX, analyzing designs from inspiration sites, generating design images with ai-multimodal, implementing visual hierarchy and color theory, adding micro-interactions, or creating design documentation. Includes workflows for capturing and analyzing inspiration screenshots with chrome-devtools and ai-multimodal, iterative design image generation until aesthetic standards are met, and comprehensive design system guidance covering BEAUTIFUL (aesthetic principles), RIGHT (functionality/accessibility), SATISFYING (micro-interactions), and PEAK (storytelling) stages. Integrates with chrome-devtools, ai-multimodal, media-processing, ui-styling, and web-frameworks skills.

**Location**: `.claude/skills/aesthetic/SKILL.md`

### 📚 `frontend-design`

Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications, OR when they provide screenshots/images/designs to replicate or draw inspiration from. For screenshot inputs, extracts design guidelines first using ai-multimodal analysis, then implements code following those guidelines. Generates creative, polished code that avoids generic AI aesthetics.

**Location**: `.claude/skills/frontend-design/SKILL.md`

### `frontend-development`

Frontend development guidelines for React/TypeScript applications. Modern patterns including Suspense, lazy loading, useSuspenseQuery, file organization with features directory, MUI v7 styling, TanStack Router, performance optimization, and TypeScript best practices. Use when creating components, pages, features, fetching data, styling, routing, or working with frontend code.

**Location**: `.claude/skills/frontend-development/SKILL.md`

### 📦 `mcp-builder`

Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

**Location**: `.claude/skills/mcp-builder/SKILL.md`

### 📚 `threejs`

Build immersive 3D web experiences with Three.js - WebGL/WebGPU library for scenes, cameras, geometries, materials, lights, animations, loaders, post-processing, shaders (including node-based TSL), compute, physics, VR/XR, and advanced rendering. Use when creating 3D visualizations, games, interactive graphics, data viz, product configurators, architectural walkthroughs, or WebGL/WebGPU applications. Covers OrbitControls, GLTF/FBX loading, PBR materials, shadow mapping, post-processing effects (bloom, SSAO, SSR), custom shaders, instancing, LOD, animation systems, and WebXR.

**Location**: `.claude/skills/threejs/SKILL.md`

### 📦 📚 `ui-styling`

Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and canvas-based visual designs. Use when building user interfaces, implementing design systems, creating responsive layouts, adding accessible components (dialogs, dropdowns, forms, tables), customizing themes and colors, implementing dark mode, generating visual designs and posters, or establishing consistent styling patterns across applications.

**Location**: `.claude/skills/ui-styling/SKILL.md`

## Infrastructure & DevOps

### 📦 📚 `devops`

Deploy and manage cloud infrastructure on Cloudflare (Workers, R2, D1, KV, Pages, Durable Objects, Browser Rendering), Docker containers, and Google Cloud Platform (Compute Engine, GKE, Cloud Run, App Engine, Cloud Storage). Use when deploying serverless functions to the edge, configuring edge computing solutions, managing Docker containers and images, setting up CI/CD pipelines, optimizing cloud infrastructure costs, implementing global caching strategies, working with cloud databases, or building cloud-native applications.

**Location**: `.claude/skills/devops/SKILL.md`

## Multimedia & Processing

### 📦 📚 `chrome-devtools`

Browser automation, debugging, and performance analysis using Puppeteer CLI scripts. Use for automating browsers, taking screenshots, analyzing performance, monitoring network traffic, web scraping, form automation, and JavaScript debugging.

**Location**: `.claude/skills/chrome-devtools/SKILL.md`

### 📦 `document-skills/docx`

Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks

**Location**: `.claude/skills/document-skills/docx/SKILL.md`

### 📦 `document-skills/pdf`

Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.

**Location**: `.claude/skills/document-skills/pdf/SKILL.md`

### 📦 `document-skills/pptx`

Presentation creation, editing, and analysis. When Claude needs to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes, or any other presentation tasks

**Location**: `.claude/skills/document-skills/pptx/SKILL.md`

### `document-skills/xlsx`

Comprehensive spreadsheet creation, editing, and analysis with support for formulas, formatting, data analysis, and visualization. When Claude needs to work with spreadsheets (.xlsx, .xlsm, .csv, .tsv, etc) for: (1) Creating new spreadsheets with formulas and formatting, (2) Reading or analyzing data, (3) Modify existing spreadsheets while preserving formulas, (4) Data analysis and visualization in spreadsheets, or (5) Recalculating formulas

**Location**: `.claude/skills/document-skills/xlsx/SKILL.md`

### 📦 📚 `media-processing`

Process multimedia files with FFmpeg (video/audio encoding, conversion, streaming, filtering, hardware acceleration), ImageMagick (image manipulation, format conversion, batch processing, effects, composition), and RMBG (AI-powered background removal). Use when converting media formats, encoding videos with specific codecs (H.264, H.265, VP9), resizing/cropping images, removing backgrounds from images, extracting audio from video, applying filters and effects, optimizing file sizes, creating streaming manifests (HLS/DASH), generating thumbnails, batch processing images, creating composite images, or implementing media processing pipelines. Supports 100+ formats, hardware acceleration (NVENC, QSV), and complex filtergraphs.

**Location**: `.claude/skills/media-processing/SKILL.md`

## Utilities & Helpers

### 📚 `code-review`

Use when receiving code review feedback (especially if unclear or technically questionable), when completing tasks or major features requiring review before proceeding, or before making any completion/success claims. Covers three practices - receiving feedback with technical rigor over performative agreement, requesting reviews via code-reviewer subagent, and verification gates requiring evidence before any status claims. Essential for subagent-driven development, pull requests, and preventing false completion claims.

**Location**: `.claude/skills/code-review/SKILL.md`

### 📦 📚 `debugging`

Systematic debugging framework ensuring root cause investigation before fixes. Includes four-phase debugging process, backward call stack tracing, multi-layer validation, and verification protocols. Use when encountering bugs, test failures, unexpected behavior, performance issues, or before claiming work complete. Prevents random fixes, masks over symptoms, and false completion claims.

**Location**: `.claude/skills/debugging/SKILL.md`

### 📚 `planning`

Use when you need to plan technical solutions that are scalable, secure, and maintainable.

**Location**: `.claude/skills/planning/SKILL.md`

### 📚 `problem-solving`

Apply systematic problem-solving techniques for complexity spirals (simplification cascades), innovation blocks (collision-zone thinking), recurring patterns (meta-pattern recognition), assumption constraints (inversion exercise), scale uncertainty (scale game), and dispatch when stuck. Techniques derived from Microsoft Amplifier project patterns adapted for immediate application.

**Location**: `.claude/skills/problem-solving/SKILL.md`

### `research`

Use when you need to research, analyze, and plan technical solutions that are scalable, secure, and maintainable.

**Location**: `.claude/skills/research/SKILL.md`

### 📦 📚 `sequential-thinking`

Apply structured, reflective problem-solving for complex tasks requiring multi-step analysis, revision capability, and hypothesis verification. Use for complex problem decomposition, adaptive planning, analysis needing course correction, problems with unclear scope, multi-step solutions, and hypothesis-driven work.

**Location**: `.claude/skills/sequential-thinking/SKILL.md`
