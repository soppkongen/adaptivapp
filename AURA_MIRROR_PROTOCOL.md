# AURA Mirror Protocol Documentation

## Core Design Ethos: "We Only Mirror"

The AURA system has been redesigned with a fundamental principle: **"We Only Mirror"**. AURA operates as a responsive mirror that only adapts what the user can already observe—attention, load, fatigue. The system does **not predict**, **diagnose**, or **intervene** unless explicitly asked.

---

## Design Principles

### 1. Responsive Mirror Operation
- AURA only adapts what the user can already observe
- No hidden agenda, no background nudging, no behavioral scoring
- The system responds like a puppy—intuitive and loyal, not judgmental

### 2. Explicit User Control
- All modes have clear toggles with explicit enable/disable switches
- Adaptive Mode is **default OFF** for privacy
- Users can see what's changing and understand why
- All changes are reversible

### 3. Privacy-First Architecture
- 100% local biometric processing
- No data transmission of sensitive information
- All metrics are opt-in only
- User-controlled data retention

---

## Dual Modes Architecture

### A. Prompted Mode (Manual Interaction)

**Always Available** - User-initiated interface modifications

#### Triggers
- User input (text, voice, button)
- Natural language commands like:
  - "Make it softer on the eyes"
  - "I want a calmer layout"
  - "Reduce the density"

#### Processing
- Translates commands to tag-based schema
- Tags: `color:calm`, `layout:minimal`, `density:low`
- Immediate, reversible UI changes

#### API Endpoints
```
POST /api/aura/prompted/command
{
  "user_id": "executive_001",
  "command": "Make it softer on the eyes",
  "session_id": "session_123"
}
```

### B. Adaptive Mode (AURA Passive Response)

**Default OFF** - Biometric-triggered interface modifications

#### Triggers
- Biometric signals: fatigue, gaze drift, tension, stress
- Only when explicitly enabled by user

#### Processing
- Gradual interface modifications based on tag weight shifts
- Reduced density, increased whitespace, softened contrast
- Always user-visible and controllable

#### API Endpoints
```
POST /api/aura/adaptive/process
{
  "user_id": "executive_001",
  "session_id": "session_123",
  "signals": [
    {"type": "fatigue", "intensity": 0.7, "confidence": 0.9}
  ]
}
```

#### User Control
```
POST /api/aura/settings/adaptive-mode
{
  "user_id": "executive_001",
  "enabled": true
}
```

---

## Metric Packaging for Power Users

All metrics are **opt-in reflection tools** designed for high-level operators who seek to track their own behavioral patterns. These **do not trigger interface changes** unless the user wants them to.

### Available Metrics

#### 1. Visual Age Delta
- Tracks facial shifts over time (local-only)
- Simple visual age estimate trendline
- Example: "+0.8 years since March"

```
GET /api/aura/metrics/visual-age-delta?user_id=executive_001
```

#### 2. Focus Heatmap
- Tracks attention across app sections
- Insight: "72% of gaze spent on non-primary KPIs"
- Delivered as toggleable overlay

```
GET /api/aura/metrics/focus-heatmap?user_id=executive_001&session_id=session_123
```

#### 3. Cognitive Drift Index
- Detects disengagement patterns
- Scrolling without reading, rapid navigation
- Insight: "You disengaged 3x faster on raw data views"

```
GET /api/aura/metrics/cognitive-drift?user_id=executive_001&session_id=session_123
```

#### 4. Entropy Score
- Measures layout changes, overrides, theme flips
- Higher score = higher personalization demand
- Used to fine-tune design defaults

```
GET /api/aura/metrics/entropy-score?user_id=executive_001
```

#### 5. Mood Resonance Profile (Explicit Opt-in Only)
- Derived from tone, expression, micro-movements
- Optional chart showing energy patterns over time
- Requires explicit consent

```
GET /api/aura/metrics/mood-resonance?user_id=executive_001
```

### Enabling Metrics
```
POST /api/aura/settings/metrics
{
  "user_id": "executive_001",
  "metrics": [
    "visual_age_delta",
    "focus_heatmap",
    "cognitive_drift_index"
  ]
}
```

---

## System Architecture

| Layer              | Purpose                      | Trigger                  | Output                | User Role |
| ------------------ | ---------------------------- | ------------------------ | --------------------- | --------- |
| Mirror (AURA Core) | Passive Interface Adaptation | Biometric Inputs         | Real-Time UI Tweaks   | Observer  |
| Prompted Edits     | Intent-Based Layout Shifts   | User Text/Voice/Button   | Tagged Visual Changes | Commander |
| Insight Packaging  | Longitudinal Self-Tracking   | Aggregated Data (Opt-In) | Visual Reports        | Analyst   |

---

## Implementation Guidelines

### 1. Strict Mode Separation
- No cross-leak between Prompted and Adaptive unless explicitly linked by user
- Each mode operates independently
- Clear boundaries and user understanding

### 2. Tag System Integration
- Every UI element maps to 1–2 descriptive tags
- Tags for style, layout, mood
- Consistent tag vocabulary across modes

### 3. Clear Toggles
- Adaptive Mode has explicit enable/disable switch
- Default state is OFF for privacy
- User education about what each mode does

### 4. Privacy Compliance
- Local-only biometric processing unless user requests otherwise
- No sensitive data transmission
- User-controlled data retention periods

### 5. Insight Delivery
- Reports are opt-in and downloadable
- Stored locally unless cloud sync is chosen
- Clear data ownership and control

---

## API Reference

### Core Endpoints

#### System Status
```
GET /api/aura/status
```
Returns system status and design principles.

#### User Initialization
```
POST /api/aura/initialize
{
  "user_id": "executive_001"
}
```

#### Settings Management
```
GET /api/aura/settings?user_id=executive_001
POST /api/aura/settings/adaptive-mode
POST /api/aura/settings/metrics
```

#### Revert Changes
```
POST /api/aura/revert
{
  "user_id": "executive_001"
}
```

#### Data Export
```
GET /api/aura/export?user_id=executive_001
```

---

## Testing

Run the comprehensive test suite:

```bash
python test_aura_mirror_protocol.py
```

The test suite validates:
- "We Only Mirror" design ethos implementation
- Dual mode separation and functionality
- Privacy compliance
- User control mechanisms
- Metric opt-in processes

---

## Privacy and Security

### Local Processing
- All biometric data processed on user's device
- No raw biometric data transmitted to servers
- Differential privacy protection

### User Control
- Explicit opt-in for all features
- Clear understanding of what data is collected
- User-controlled retention and deletion

### Compliance
- GDPR compliant by design
- Enterprise security standards
- Audit trail for all user interactions

---

## Integration Example

```javascript
// Initialize AURA for user
const response = await fetch('/api/aura/initialize', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: 'executive_001'})
});

// Process user command
const commandResponse = await fetch('/api/aura/prompted/command', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 'executive_001',
    command: 'Make it calmer',
    session_id: 'current_session'
  })
});

// Enable adaptive mode (user choice)
const adaptiveResponse = await fetch('/api/aura/settings/adaptive-mode', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_id: 'executive_001',
    enabled: true
  })
});
```

---

## Conclusion

The AURA Mirror Protocol implements a revolutionary approach to human-computer interaction that respects user autonomy while providing intelligent adaptation. By following the "We Only Mirror" design ethos, AURA becomes an intuitive, loyal companion for executive decision-making rather than a judgmental or manipulative system.

The system's dual-mode architecture, privacy-first design, and opt-in metrics create a foundation for truly symbiotic human-AI collaboration in enterprise environments.

