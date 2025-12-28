# Centralized Environment Variable Resolution

## Overview

All Claude Code skills now use a centralized environment variable resolver (`~/.claude/scripts/resolve_env.py`) for consistent configuration management across project-local and user-global scopes.

## Priority Hierarchy

Environment variables are resolved in this order (highest to lowest):

1. **process.env** - Runtime environment variables (HIGHEST)
2. **PROJECT/.claude/skills/\<skill\>/.env** - Project skill-specific overrides
3. **PROJECT/.claude/skills/.env** - Project shared across all skills
4. **PROJECT/.claude/.env** - Project global defaults
5. **~/.claude/skills/\<skill\>/.env** - User skill-specific overrides
6. **~/.claude/skills/.env** - User shared across all skills
7. **~/.claude/.env** - User global defaults (LOWEST)

## Benefits

### 1. **Consistency**
All skills use the same resolution logic - no more divergent implementations.

### 2. **Flexibility**
Supports both project-local and user-global configurations:
- **Project-local** (`.claude/` in project): Version-controlled, team-shared defaults
- **User-global** (`~/.claude/`): Personal overrides, API keys, machine-specific config

### 3. **Debuggability**
Built-in tools for troubleshooting:
```bash
# Show hierarchy for specific skill
python ~/.claude/scripts/resolve_env.py --show-hierarchy --skill ai-multimodal

# Find where variable is defined
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --find-all

# Resolve with verbose output
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --skill ai-multimodal --verbose
```

### 4. **Maintainability**
Single source of truth - update once, affects all skills.

## Usage

### CLI Usage

```bash
# Resolve variable for specific skill
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --skill ai-multimodal

# With default value
python ~/.claude/scripts/resolve_env.py API_KEY --default fallback-value

# Export format for shell
eval $(python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --export)

# Show hierarchy
python ~/.claude/scripts/resolve_env.py --show-hierarchy --skill ai-multimodal
```

### Python API Usage

```python
import sys
from pathlib import Path

# Import centralized resolver
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))
from resolve_env import resolve_env

# Resolve API key
api_key = resolve_env('GEMINI_API_KEY', skill='ai-multimodal')

if not api_key:
    print("Error: GEMINI_API_KEY not found")
    sys.exit(1)

# Use api_key...
```

### Integration in Skills

Skills automatically use the centralized resolver with fallback:

```python
# Import centralized environment resolver
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))
try:
    from resolve_env import resolve_env
    CENTRALIZED_RESOLVER_AVAILABLE = True
except ImportError:
    CENTRALIZED_RESOLVER_AVAILABLE = False
    # Fallback to legacy resolution...

def find_api_key() -> Optional[str]:
    if CENTRALIZED_RESOLVER_AVAILABLE:
        return resolve_env('GEMINI_API_KEY', skill='skill-name')
    # Fallback logic...
```

## Common Scenarios

### Scenario 1: Global Default
```bash
# ~/.claude/.env
GEMINI_API_KEY=my-personal-key
```
Result: All skills use `my-personal-key` by default.

### Scenario 2: Project Override
```bash
# ~/.claude/.env
GEMINI_API_KEY=personal-key

# PROJECT/.claude/.env
GEMINI_API_KEY=team-shared-key
```
Result: When working in PROJECT, skills use `team-shared-key`.

### Scenario 3: Skill-Specific Override
```bash
# ~/.claude/.env
GEMINI_API_KEY=default-key

# ~/.claude/skills/ai-multimodal/.env
GEMINI_API_KEY=high-quota-key
```
Result: ai-multimodal uses `high-quota-key`, other skills use `default-key`.

### Scenario 4: Runtime Testing
```bash
export GEMINI_API_KEY=test-key
python script.py
```
Result: All skills use `test-key` regardless of config files.

## Debugging

### Check Hierarchy
```bash
python ~/.claude/scripts/resolve_env.py --show-hierarchy --skill ai-multimodal
```

Output shows which config files exist (✓) and their priority:
```
Environment Variable Resolution Hierarchy
============================================================

Priority order (highest to lowest):
1. process.env - Runtime environment
2. Project skill-specific (ai-multimodal) ✗ /path/to/project/.claude/skills/ai-multimodal/.env
3. Project skills shared          ✓ /path/to/project/.claude/skills/.env
4. Project global                 ✓ /path/to/project/.claude/.env
5. User skill-specific (ai-multimodal) ✗ /Users/user/.claude/skills/ai-multimodal/.env
6. User skills shared             ✓ /Users/user/.claude/skills/.env
7. User global                    ✓ /Users/user/.claude/.env
```

### Find All Locations
```bash
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --find-all
```

Shows everywhere the variable is defined and which one wins:
```
Variable 'GEMINI_API_KEY' found in 2 location(s):
============================================================

2. Project global
   Path: /path/to/project/.claude/.env
   Value: AIza...FJI

7. User global
   Path: /Users/user/.claude/.env
   Value: AIza...XYZ

============================================================
✓ Resolved value (highest priority): AIza...FJI
```

### Verbose Resolution
```bash
python ~/.claude/scripts/resolve_env.py GEMINI_API_KEY --skill ai-multimodal --verbose
```

Shows step-by-step where the resolver looks:
```
✗ GEMINI_API_KEY not in: Runtime environment
✗ GEMINI_API_KEY not in: Project skill-specific (ai-multimodal) (file not found)
✓ GEMINI_API_KEY found in: Project skills shared
  Path: /path/to/project/.claude/skills/.env
```

## Migration Guide

### For Existing Skills

1. Keep existing `find_api_key()` function as fallback
2. Add centralized resolver import at top:
```python
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))
try:
    from resolve_env import resolve_env
    CENTRALIZED_RESOLVER_AVAILABLE = True
except ImportError:
    CENTRALIZED_RESOLVER_AVAILABLE = False
```

3. Update resolution logic:
```python
def find_api_key() -> Optional[str]:
    if CENTRALIZED_RESOLVER_AVAILABLE:
        return resolve_env('GEMINI_API_KEY', skill='skill-name')
    # Keep fallback logic for backward compatibility
```

### For New Skills

Simply use the centralized resolver directly:
```python
from resolve_env import resolve_env

api_key = resolve_env('API_KEY_NAME', skill='skill-name')
```

## Files Created

1. **~/.claude/scripts/resolve_env.py** - Centralized resolver implementation
2. **~/.claude/scripts/README.md** - Detailed usage documentation
3. **.claude/ENVIRONMENT_RESOLVER.md** (this file) - Project documentation

## Updated Files

1. **.claude/.env.example** - Added resolver reference
2. **.claude/skills/.env.example** - Added resolver reference
3. **.claude/skills/ai-multimodal/.env.example** - Added resolver reference
4. **.claude/skills/ai-multimodal/scripts/gemini_batch_process.py** - Integrated resolver
5. **.claude/skills/ai-multimodal/SKILL.md** - Updated documentation

## Next Steps

1. **Test the resolver** with your actual API keys
2. **Update other skills** to use centralized resolver
3. **Create config files** as needed:
   - `~/.claude/.env` for personal defaults
   - `.claude/.env` in projects for team defaults
   - `.claude/skills/<skill>/.env` for skill-specific overrides

## Support

- Documentation: `~/.claude/scripts/README.md`
- Show hierarchy: `python ~/.claude/scripts/resolve_env.py --show-hierarchy`
- Debug variable: `python ~/.claude/scripts/resolve_env.py VAR_NAME --verbose`
