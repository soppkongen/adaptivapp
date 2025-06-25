# Command Reflex Layer Documentation

## Final Unified System for Elite Commander Dashboard

The Command Reflex Layer represents the culmination of AURA development - a unified, simplified system that eliminates redundancy and focuses on the core mission: **enhancing decision velocity for Elite Commanders**.

---

## Core Mission

**Elite Commander superuser dashboard with responsive logic to make oversight frictionless.**

This is not a feel-good mirror tool. It's a **superuser command dashboard** where the feedback/adaptive components must **enhance decision velocity**, not distract.

---

## Unified Architecture: Command Reflex Layer

### Context-Aware System Responsiveness Across Three Tiers

#### 1. **Passive Tier** (AURA biometric-reactive)
- **Default**: OFF (privacy-first)
- **Function**: Continuous biometric monitoring with gradual interface adaptation
- **Triggers**: Fatigue, stress, eye strain, attention drift
- **Processing**: 100% local, system-facing only
- **User Control**: Explicit enable/disable toggle

#### 2. **Semi-Active Tier** (Mirror suggestions)
- **Default**: ON
- **Function**: Conversational feedback system with immediate adaptation
- **Triggers**: User feedback like "Too noisy", "Feels sharp"
- **Processing**: Natural language to UI tag conversion
- **User Control**: Always available, reversible

#### 3. **Active Tier** (Direct commands)
- **Default**: ON
- **Function**: Element-specific command processing
- **Triggers**: Direct commands like "Make this card smaller"
- **Processing**: Targeted UI element modification
- **User Control**: Immediate execution, full reversibility

---

## Simplified Entry Modes

### Three Entry Modes Replace Complex Interaction Categories

#### 1. **Mirror Mode** (Semi-Active Tier)
**Freeform feedback + adaptation**
- Input: "Too noisy", "Feels sharp", "Make it calmer"
- Processing: Natural language → tag changes → UI adaptation
- Scope: Global interface adjustments
- API: `POST /api/reflex/mirror`

#### 2. **Edit Mode** (Active Tier)
**Element-specific commands**
- Input: "Make this card smaller", "Hide this panel"
- Processing: Target identification → specific element modification
- Scope: Individual UI elements
- API: `POST /api/reflex/edit`

#### 3. **Observe Mode** (Passive Tier)
**Passive biometric reflection**
- Input: Biometric signals (fatigue, stress, attention)
- Processing: Signal analysis → gradual adaptation
- Scope: System-wide comfort optimization
- API: `POST /api/reflex/observe`

---

## Clear Metrics Separation

### System-Facing Metrics (Invisible to User)
**Purpose**: Internal adaptation optimization only

- **Command Effectiveness**: Success rate of adaptations
- **Tier Usage Patterns**: Which tiers are most effective
- **Adaptation Frequency**: How often changes are needed
- **Conflict Resolution**: Tag conflict patterns

**Privacy**: Never exposed to user, aggregated only

### User-Facing Wellness Metrics (Opt-in Only)
**Purpose**: Self-reflection and insight tools

- **Digital Fatigue**: "Your fatigue patterns show increased strain during afternoon sessions"
- **Attention Pattern**: "You maintain focus best during 25-minute intervals"
- **Stress Trend**: Weekly stress pattern visualization
- **Focus Optimization**: Personalized focus recommendations

**Control**: Explicit opt-in required, user-controlled retention

---

## Technical Implementation

### Tag System (`tags.json`)
```json
{
  "categories": {
    "style": ["sharp", "smooth", "soft", "harsh", "calm", "energetic"],
    "layout": ["dense", "open", "spacious", "compact", "focused", "minimal"],
    "density": ["light", "heavy", "thin", "thick"],
    "mood": ["relaxed", "alert", "urgent", "passive"]
  },
  "conflict_resolution": {
    "strategy": "weighted_reduction",
    "reduction_factor": 0.7
  }
}
```

### Layout Tree (`layout_tree.json`)
```json
{
  "elements": {
    "elite_dashboard": {
      "type": "container",
      "children": ["command_header", "executive_overview", "portfolio_grid"],
      "adaptation_priority": "high"
    },
    "command_header": {
      "type": "panel",
      "children": ["metrics_bar", "alert_center", "command_controls"],
      "adaptation_priority": "high"
    }
  }
}
```

### Prompt Parser
- **Input**: Natural language commands
- **Processing**: Pattern matching → intent extraction → tag mapping
- **Output**: Structured tag changes with confidence scores

### Adaptation Engine
- **Tag Application**: Element-specific tag weight updates
- **Conflict Resolution**: Automatic handling of conflicting tags
- **Propagation**: Parent-to-child tag inheritance (configurable)

---

## API Reference

### Core Endpoints

#### System Status
```
GET /api/reflex/status
```
Returns system information and mission focus.

#### User Initialization
```
POST /api/reflex/initialize
{
  "user_id": "elite_commander_001"
}
```

#### Mirror Mode (Semi-Active)
```
POST /api/reflex/mirror
{
  "user_id": "elite_commander_001",
  "feedback": "Too harsh on the eyes"
}
```

#### Edit Mode (Active)
```
POST /api/reflex/edit
{
  "user_id": "elite_commander_001",
  "command": "Make this card smaller",
  "target_element": "kpi_summary"
}
```

#### Observe Mode (Passive)
```
POST /api/reflex/observe
{
  "user_id": "elite_commander_001",
  "signals": [
    {"type": "fatigue", "intensity": 0.8, "confidence": 0.9}
  ]
}
```

#### Tier Management
```
POST /api/reflex/tiers/{tier_name}
{
  "user_id": "elite_commander_001",
  "enabled": true
}
```

#### Wellness Insights (Opt-in)
```
POST /api/reflex/wellness/enable
{
  "user_id": "elite_commander_001",
  "insight_types": ["digital_fatigue", "attention_pattern"]
}

GET /api/reflex/wellness/{insight_type}?user_id=elite_commander_001
```

#### Layout State
```
GET /api/reflex/layout?user_id=elite_commander_001
```

#### Revert Changes
```
POST /api/reflex/revert
{
  "user_id": "elite_commander_001"
}
```

---

## Elite Commander Dashboard Elements

### Command Header
- **Metrics Bar**: Real-time portfolio KPIs
- **Alert Center**: Critical notifications (high adaptation priority)
- **Command Controls**: Executive action buttons

### Executive Overview
- **KPI Summary**: Key performance indicators
- **Trend Analysis**: Portfolio trend visualization
- **Risk Indicators**: Risk assessment display

### Portfolio Grid
- **Company Cards**: Individual company status
- **Performance Charts**: Visual performance data
- **Action Items**: Executive tasks and priorities

### Command Sidebar
- **Quick Actions**: Rapid executive commands
- **Intelligence Feed**: Real-time updates
- **System Status**: Health indicators

---

## Adaptation Rules

### Biometric Signal Mapping
- **Fatigue** → Increase: soft, calm, light, spacious
- **Stress** → Increase: calm, smooth, relaxed, minimal
- **Eye Strain** → Increase: soft, light, spacious
- **Attention Drift** → Increase: focused, minimal, alert

### Command Pattern Recognition
- "Too harsh" → smooth, calm
- "Too noisy" → minimal, open
- "Hard to focus" → focused, minimal
- "Too crowded" → open, spacious

### Priority-Based Adaptation
- **Critical Elements**: Alert center, risk indicators (100% adaptation strength)
- **High Priority**: Command controls, KPI summary (80% strength)
- **Medium Priority**: Portfolio grid, sidebar (60% strength)
- **Low Priority**: System status, charts (40% strength)

---

## Privacy and Security

### Local Processing
- All biometric data processed on user's device
- No raw biometric transmission to servers
- System metrics aggregated only, never individual data

### User Control
- Explicit opt-in for all features
- Passive tier default OFF
- All changes reversible
- User-controlled data retention

### Compliance
- GDPR compliant by design
- Enterprise security standards
- Complete audit trail

---

## Testing

Run the comprehensive test suite:
```bash
python test_command_reflex_layer.py
```

Tests validate:
- Unified system architecture
- Three-tier functionality
- Entry mode processing
- Metrics separation
- Privacy compliance
- Elite Commander mission focus

---

## Integration Example

```javascript
// Initialize Command Reflex Layer
const response = await fetch('/api/reflex/initialize', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: 'elite_commander_001'})
});

// Process mirror feedback
const mirrorResponse = await fetch('/api/reflex/mirror', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 'elite_commander_001',
    feedback: 'Interface feels too harsh'
  })
});

// Enable passive tier (user choice)
const passiveResponse = await fetch('/api/reflex/tiers/passive', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 'elite_commander_001',
    enabled: true
  })
});
```

---

## Key Improvements from Previous Versions

### 1. **Eliminated Redundancy**
- Single unified system instead of competing subsystems
- Clear tier separation without overlap
- Simplified interaction model

### 2. **Focused Mission**
- Elite Commander dashboard focus
- Decision velocity enhancement
- Removed feel-good mirror tool aspects

### 3. **Clarified Metrics**
- Hard separation: system vs user-facing
- Opt-in only for user-facing insights
- Privacy-first design

### 4. **Simplified Interactions**
- Three clear entry modes
- Reduced complexity from multiple input categories
- Intuitive command processing

### 5. **Enhanced Control**
- Explicit toggles for all features
- Default privacy-first settings
- Complete user autonomy

---

## Conclusion

The Command Reflex Layer represents the final evolution of the AURA system - a unified, focused, and powerful tool for Elite Commanders. By eliminating redundancy, clarifying the mission, and simplifying interactions, the system now truly serves its purpose: **enhancing decision velocity through responsive, intelligent interface adaptation**.

The system maintains the revolutionary biometric capabilities while ensuring privacy, user control, and mission focus. It's no longer a mirror tool - it's a command enhancement system for elite decision-makers.

