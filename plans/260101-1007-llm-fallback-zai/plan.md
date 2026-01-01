# Implementation Plan: LLM API Config Check with ZAI Fallback

**Date:** 2026-01-01
**Plan ID:** 260101-1007-llm-fallback-zai
**Status:** Draft
**Complexity:** Medium

---

## Executive Summary

Implement intelligent LLM provider fallback system with API configuration checking. When Claude/DeepSeek APIs are not configured, automatically fallback to ZAI's GLM-4-Flash model (OpenAI-compatible). System supports user-defined provider priority with ZAI as ultimate fallback.

**User Requirements:**
- Check Claude/DeepSeek API config at runtime
- Fallback to ZAI GLM-4-Flash when APIs not configured
- Add `ZAI_API_KEY` environment variable
- Support user choice with ZAI as ultimate fallback

**Implementation Impact:**
- Modified files: 3 (config.py, ai_summarizer.py, .env.example)
- New functionality: Provider availability checking, intelligent fallback chain
- Testing: Unit tests for fallback logic

---

## Current Architecture Analysis

### Existing LLM Integration (backend/app/advisor/ai_summarizer.py:137-567)

**Current Flow:**
```python
class AISummarizer:
    def __init__(
        anthropic_api_key: str,
        deepseek_api_key: str,
        default_model: str = "claude"
    ):
        self._anthropic_client = None  # Lazy init
        self._openai_client = None     # Lazy init
```

**Current Behavior:**
- Lazy initialization of clients (lines 166-187)
- `default_model` param determines primary LLM ("claude" or "deepseek")
- **NO fallback logic** - if primary fails, raises exception
- DeepSeek uses OpenAI SDK with `base_url="https://api.deepseek.com"` (line 183)

**Current Config (backend/app/config.py:36-39):**
```python
ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'claude')
```

### Identified Gaps

1. **No availability checking** - clients initialized even if API keys empty
2. **No fallback chain** - single model selection, no graceful degradation
3. **Hard failure mode** - RuntimeError if primary unavailable (line 349)
4. **No ZAI integration** - no third provider option

---

## Solution Design

### Architecture: Intelligent Provider Fallback Chain

```
┌─────────────────────────────────────────────────────────────┐
│             LLM Request (generate_summary)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Check Available Providers  │
        │  - Claude: has API key?     │
        │  - DeepSeek: has API key?   │
        │  - ZAI: has API key?        │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Build Priority Chain      │
        │   User Config → ZAI         │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Try providers in order    │
        │   1. User's DEFAULT_LLM     │
        │   2. ZAI (if API key set)   │
        │   3. Error fallback         │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Return AI Response        │
        └────────────────────────────┘
```

### Key Design Decisions

**1. Provider Availability Check**
- **When:** On `AISummarizer` initialization
- **How:** Check if API key is non-empty string
- **Cache:** Store availability flags to avoid repeated checks

**2. Fallback Priority**
- **User's DEFAULT_LLM_MODEL** (claude/deepseek/zai)
- **ZAI GLM-4-Flash** (if ZAI_API_KEY configured)
- **Error Response** (graceful degradation with static fallback)

**3. ZAI Integration Method**
- **Reuse OpenAI SDK** - GLM-4.7 is OpenAI-compatible
- **Base URL:** `https://api.z.ai/api/paas/v4`
- **Model Name:** `glm-4-flash` or `glm-4.7`
- **No new dependencies** - leverage existing `openai` package

---

## Implementation Phases

### Phase 1: Config Layer Enhancement

**File:** `backend/app/config.py`

**Changes:**
```python
# Add new env var
ZAI_API_KEY: str = os.getenv('ZAI_API_KEY', '')

# Optional: Allow DEFAULT_LLM_MODEL to accept "zai"
# DEFAULT_LLM_MODEL: "claude" | "deepseek" | "zai"
```

**File:** `backend/.env.example`

**Changes:**
```bash
# LLM API Keys (Phase 04 - AI Recommendations)
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
ZAI_API_KEY=
DEFAULT_LLM_MODEL=claude  # Options: claude, deepseek, zai
```

**Validation:**
- ✅ Env var loads correctly
- ✅ Config dataclass updated
- ✅ No breaking changes to existing code

---

### Phase 2: AISummarizer Provider Management

**File:** `backend/app/advisor/ai_summarizer.py`

**Changes:**

**2.1. Add Provider Availability Tracking**
```python
class AISummarizer:
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        zai_api_key: Optional[str] = None,  # NEW
        default_model: str = "claude",
        redis_client=None
    ):
        self.anthropic_key = anthropic_api_key
        self.deepseek_key = deepseek_api_key
        self.zai_key = zai_api_key  # NEW
        self.default_model = default_model
        self.redis = redis_client

        # Track availability
        self.available_providers = self._check_available_providers()  # NEW

    def _check_available_providers(self) -> List[str]:
        """Check which LLM providers have valid API keys."""
        providers = []
        if self.anthropic_key:
            providers.append("claude")
        if self.deepseek_key:
            providers.append("deepseek")
        if self.zai_key:
            providers.append("zai")
        return providers
```

**2.2. Add ZAI Client Initialization**
```python
def _get_zai_client(self):
    """Lazy initialization of ZAI client (OpenAI-compatible)."""
    if self._zai_client is None and self.zai_key:
        try:
            from openai import OpenAI
            self._zai_client = OpenAI(
                api_key=self.zai_key,
                base_url="https://api.z.ai/api/paas/v4"
            )
        except ImportError:
            logger.warning("openai package not installed")
    return self._zai_client
```

**2.3. Add ZAI API Call Method**
```python
async def _call_zai(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """Call ZAI GLM-4-Flash API (OpenAI-compatible).

    Args:
        prompt: The prompt to send to ZAI
        max_tokens: Maximum tokens in response (default: 500)
        temperature: Sampling temperature 0.0-2.0 (default: 0.7)
    """
    client = self._get_zai_client()
    if client is None:
        raise RuntimeError("ZAI client not available")

    def _sync_call():
        response = client.chat.completions.create(
            model="glm-4-flash",  # Fast, cost-effective model
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "You are a technical analysis expert. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    return await asyncio.to_thread(_sync_call)
```

**2.4. Implement Intelligent Fallback Chain**
```python
async def generate_summary(
    self,
    analysis_data: Dict[str, Any],
    language: str = "vi",
    use_cache: bool = True,
    model: Optional[str] = None,
    temperature: float = 0.5
) -> Dict[str, Any]:
    """Generate AI summary with intelligent fallback."""

    # Determine provider priority
    requested_model = model or self.default_model
    fallback_chain = self._build_fallback_chain(requested_model)

    # Check cache first
    if use_cache:
        cache_key = self._generate_cache_key(analysis_data)
        cached = await self._check_cache(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    # Build prompt
    prompt = self._build_prompt(analysis_data, language)

    # Try providers in order
    last_error = None
    for provider in fallback_chain:
        try:
            logger.info(f"Attempting LLM call with provider: {provider}")

            if provider == "claude":
                response = await self._call_anthropic(prompt, max_tokens=500, temperature=temperature)
            elif provider == "deepseek":
                response = await self._call_deepseek(prompt, max_tokens=500, temperature=temperature)
            elif provider == "zai":
                response = await self._call_zai(prompt, max_tokens=500, temperature=temperature)
            else:
                continue

            # Parse and return successful response
            result = self._parse_response(response)
            result["model"] = provider
            result["language"] = language
            result["cached"] = False
            result["generated_at"] = datetime.utcnow().isoformat()

            # Save to cache
            if use_cache:
                await self._save_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.warning(f"Provider {provider} failed: {e}")
            last_error = e
            continue

    # All providers failed - return error fallback
    logger.exception(f"All LLM providers failed. Last error: {last_error}")
    return {
        "error": str(last_error),
        "summary": "Unable to generate AI summary - all providers unavailable",
        "signal": "HOLD",
        "confidence": 0,
        "reasoning": "AI service unavailable",
        "model": "fallback",
        "providers_tried": fallback_chain
    }

def _build_fallback_chain(self, requested_model: str) -> List[str]:
    """Build provider fallback chain based on requested model and availability.

    Priority:
    1. User's requested model (if available)
    2. ZAI (if available and not already tried)
    3. Any other available provider

    Returns:
        List of provider names in priority order
    """
    chain = []

    # Add requested model first (if available)
    if requested_model in self.available_providers:
        chain.append(requested_model)

    # Add ZAI as fallback if available and not already in chain
    if "zai" in self.available_providers and "zai" not in chain:
        chain.append("zai")

    # Add any remaining available providers
    for provider in self.available_providers:
        if provider not in chain:
            chain.append(provider)

    return chain
```

**2.5. Update Portfolio Advice Method**
Apply same fallback logic to `generate_portfolio_advice()` method (lines 413-532).

**Changes:**
- Replace hardcoded Claude → DeepSeek fallback (lines 478-487)
- Use `_build_fallback_chain()` method
- Try providers in order with same error handling

**Validation:**
- ✅ Fallback chain builds correctly based on available providers
- ✅ ZAI client initializes when API key present
- ✅ API calls succeed with correct base_url and model name
- ✅ Error handling graceful when all providers fail

---

### Phase 3: Integration & Testing

**3.1. Update Initialization Points**

**File:** `backend/app/events/advisor_events.py`
**Lines:** Where `AISummarizer` is instantiated

**Change:**
```python
# OLD:
summarizer = AISummarizer(
    anthropic_api_key=config.ANTHROPIC_API_KEY,
    deepseek_api_key=config.DEEPSEEK_API_KEY,
    default_model=config.DEFAULT_LLM_MODEL,
    redis_client=redis_client
)

# NEW:
summarizer = AISummarizer(
    anthropic_api_key=config.ANTHROPIC_API_KEY,
    deepseek_api_key=config.DEEPSEEK_API_KEY,
    zai_api_key=config.ZAI_API_KEY,  # ADD
    default_model=config.DEFAULT_LLM_MODEL,
    redis_client=redis_client
)
```

**3.2. Unit Tests**

**File:** `backend/tests/test_ai_summarizer.py` (create if not exists)

**Test Cases:**
```python
import pytest
from app.advisor.ai_summarizer import AISummarizer

class TestProviderFallback:
    def test_build_fallback_chain_claude_primary(self):
        """Test fallback chain when Claude is primary."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )
        chain = summarizer._build_fallback_chain("claude")
        assert chain == ["claude", "zai"]

    def test_build_fallback_chain_no_primary_zai_fallback(self):
        """Test ZAI fallback when primary unavailable."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )
        chain = summarizer._build_fallback_chain("claude")
        assert chain == ["zai"]

    def test_available_providers_all_configured(self):
        """Test provider availability detection."""
        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            deepseek_api_key="sk-xxx",
            zai_api_key="sk-zai-xxx"
        )
        assert set(summarizer.available_providers) == {"claude", "deepseek", "zai"}

    def test_available_providers_only_zai(self):
        """Test when only ZAI configured."""
        summarizer = AISummarizer(
            anthropic_api_key="",
            deepseek_api_key="",
            zai_api_key="sk-zai-xxx"
        )
        assert summarizer.available_providers == ["zai"]

    @pytest.mark.asyncio
    async def test_generate_summary_fallback_to_zai(self, mocker):
        """Test fallback from Claude to ZAI on error."""
        # Mock Claude to fail
        mocker.patch.object(
            AISummarizer,
            '_call_anthropic',
            side_effect=Exception("Claude API error")
        )

        # Mock ZAI to succeed
        mocker.patch.object(
            AISummarizer,
            '_call_zai',
            return_value='{"summary": "Test", "signal": "BUY", "confidence": 75, "reasoning": "..."}'
        )

        summarizer = AISummarizer(
            anthropic_api_key="sk-ant-xxx",
            zai_api_key="sk-zai-xxx",
            default_model="claude"
        )

        result = await summarizer.generate_summary(
            {"symbol": "XAUUSD", "timeframe": "H1", "price": 2650},
            use_cache=False
        )

        assert result["model"] == "zai"
        assert result["signal"] == "BUY"
```

**3.3. Integration Test**

**Scenario:** Real API call fallback test (manual testing)

**Steps:**
1. Set only `ZAI_API_KEY` in `.env`
2. Request analysis with `DEFAULT_LLM_MODEL=claude`
3. Verify system falls back to ZAI
4. Check logs for "Attempting LLM call with provider: zai"

---

## File Changes Summary

| File | Lines | Change Type | Complexity |
|------|-------|-------------|------------|
| `backend/app/config.py` | +1 | Add env var | Low |
| `backend/.env.example` | +2 | Documentation | Low |
| `backend/app/advisor/ai_summarizer.py` | +80 | New methods + refactor | Medium |
| `backend/app/events/advisor_events.py` | +1 | Constructor param | Low |
| `backend/tests/test_ai_summarizer.py` | +60 | New test file | Medium |

**Total:** 5 files, ~144 lines added

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| ZAI API incompatibility | Medium | Verify OpenAI SDK compatibility via test | Pending |
| Fallback chain incorrect priority | Low | Unit tests for chain building logic | Planned |
| Performance degradation from retries | Low | Fast-fail on unavailable providers | Design |
| Cost increase from ZAI usage | Low | ZAI priced competitively (~$0.001/1K tokens) | Acceptable |

### Operational Risks

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| ZAI API key not configured | High | Graceful error message, fallback to static | Design |
| Rate limiting across providers | Medium | Log provider switches, monitor usage | Monitoring |

---

## Acceptance Criteria

### Functional Requirements

- [ ] **FR-1:** ZAI_API_KEY env var added to config
- [ ] **FR-2:** AISummarizer accepts `zai_api_key` parameter
- [ ] **FR-3:** `_check_available_providers()` correctly identifies configured providers
- [ ] **FR-4:** `_build_fallback_chain()` constructs correct priority order
- [ ] **FR-5:** ZAI client initializes with correct base_url (`https://api.z.ai/api/paas/v4`)
- [ ] **FR-6:** `_call_zai()` method successfully calls GLM-4-Flash API
- [ ] **FR-7:** `generate_summary()` attempts providers in fallback order
- [ ] **FR-8:** System falls back to ZAI when Claude/DeepSeek unavailable
- [ ] **FR-9:** Error response returned when all providers fail
- [ ] **FR-10:** `generate_portfolio_advice()` uses same fallback logic

### Non-Functional Requirements

- [ ] **NFR-1:** No breaking changes to existing API
- [ ] **NFR-2:** Performance <100ms overhead for provider checking
- [ ] **NFR-3:** Logs indicate which provider used for each request
- [ ] **NFR-4:** Unit test coverage >80% for new code
- [ ] **NFR-5:** Documentation updated in code comments

### Testing Requirements

- [ ] **TR-1:** Unit tests for `_check_available_providers()`
- [ ] **TR-2:** Unit tests for `_build_fallback_chain()` with various configs
- [ ] **TR-3:** Mock test for fallback from Claude → ZAI
- [ ] **TR-4:** Mock test for all providers failing
- [ ] **TR-5:** Integration test with real ZAI API (manual)

---

## Implementation Sequence

**Total Estimated Effort:** 2-3 hours

### Step 1: Config Layer (20 min)
1. Add `ZAI_API_KEY` to `config.py`
2. Update `.env.example`
3. Verify config loads correctly

### Step 2: AISummarizer Core (60 min)
1. Add `zai_api_key` parameter to `__init__`
2. Implement `_check_available_providers()`
3. Implement `_get_zai_client()`
4. Implement `_call_zai()`
5. Implement `_build_fallback_chain()`
6. Refactor `generate_summary()` with fallback loop

### Step 3: Portfolio Advice (20 min)
1. Apply same fallback logic to `generate_portfolio_advice()`

### Step 4: Integration Points (10 min)
1. Update `AISummarizer` instantiation in event handlers

### Step 5: Testing (50 min)
1. Write unit tests (5 test cases)
2. Run tests, fix issues
3. Manual integration test with real API

---

## ZAI API Integration Reference

**Based on web research:**

### API Endpoint
```
Base URL: https://api.z.ai/api/paas/v4
Endpoint: /chat/completions
```

### Authentication
```python
headers = {
    "Authorization": f"Bearer {ZAI_API_KEY}",
    "Content-Type": "application/json"
}
```

### Model Names
- `glm-4-flash` - Fast, cost-effective (recommended for fallback)
- `glm-4.7` - Full model

### Request Format (OpenAI Compatible)
```python
{
    "model": "glm-4-flash",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "max_tokens": 500,
    "temperature": 0.7
}
```

### Python SDK Usage
```python
from openai import OpenAI

client = OpenAI(
    api_key=ZAI_API_KEY,
    base_url="https://api.z.ai/api/paas/v4"
)

response = client.chat.completions.create(
    model="glm-4-flash",
    messages=[{"role": "user", "content": "..."}]
)
```

**Sources:**
- [GLM-4.7 - Z.AI Developer Documentation](https://docs.z.ai/guides/llm/glm-4.7)
- [How to Access the GLM-4.7 API in 2025](https://apidog.com/blog/glm-4-7-api/)
- [GLM-4.7 on OpenRouter](https://openrouter.ai/z-ai/glm-4.7)

---

## Rollback Plan

If issues arise:

1. **Revert config.py:** Remove `ZAI_API_KEY` line
2. **Revert ai_summarizer.py:** Remove ZAI-related methods
3. **Revert .env.example:** Remove ZAI documentation
4. **System reverts to:** Original Claude/DeepSeek only behavior

**No data loss risk** - changes are additive, no existing functionality removed.

---

## Future Enhancements

1. **Provider Health Monitoring:** Track success/failure rates per provider
2. **Dynamic Provider Selection:** Choose based on latency, cost, availability
3. **Configurable Fallback Order:** ENV var to define custom priority (e.g., `LLM_FALLBACK_ORDER=deepseek,zai,claude`)
4. **Provider-Specific Caching:** Separate cache TTL per provider based on cost
5. **Multi-Provider Parallel Requests:** Race multiple providers for lowest latency

---

## Conclusion

This plan implements intelligent LLM provider fallback with ZAI GLM-4-Flash as ultimate failsafe. Design prioritizes:

- **Reliability:** Graceful degradation when primary providers fail
- **Flexibility:** User choice for primary provider
- **Simplicity:** Reuse existing OpenAI SDK, minimal new code
- **Observability:** Clear logging of provider selection

Implementation is low-risk with no breaking changes to existing functionality.

---

**Plan Status:** Ready for Implementation
**Next Steps:** Review plan → Implement Phase 1 → Test → Deploy
**Questions:** None identified
