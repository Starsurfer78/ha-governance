HA Governance – Deterministic Control Layer for Home Assistant

Version 0.1

🧠 Purpose

HA Governance is the deterministic safety and validation layer of your home.  
It acts as the control boundary beneath any local “Jarvis”-style orchestrator.

It is **not**:

- an orchestrator
- an intent system
- a planner
- a comfort engine

It **is**:

- a global state and safety authority
- a deterministic policy layer below automations and AI

🏗 Architectural role

Layered system:

- Automation layer      → triggers and flows
- Jarvis orchestrator   → decisions and planning (optional)
- HA Governance         → global state and safety policies
- Home Assistant Core   → state machine

Governance runs in parallel to automations and overrides actions when global rules are violated.

🔐 Design principles

- deterministic – no probabilistic logic
- no triggers – state-based rules only
- no multi-step workflows
- no comfort optimization
- explicit entity mapping
- priority-based enforcement

📊 Priority system

Priority  | Category  
100       | critical safety  
90–95     | protection  
70–85     | energy  
40–65     | comfort limits  

Rule: Safety > Energy > Comfort

🏠 Room-based policies

Every policy must be associated with a clearly defined room.

Example:

- name: heating_window_protection_wohnzimmer

Not allowed:

- wildcards like `climate.*`
- global window rules
- implicit room logic

🪟 Window aggregation

If a room has multiple windows, use a dedicated template binary sensor:

`binary_sensor.window_<room>_any_open`

Policies should reference only this aggregated sensor.

Reasons:

- clear mapping
- debuggable in HA state
- scalable
- orchestrator-friendly

🔥 Heating protection rule (example)
- name: heating_window_protection_wohnzimmer
  priority: 95
  when:
    binary_sensor.window_wohnzimmer_any_open: "on"
    climate.wohnzimmer: "heat"
  enforce:
    service: climate.turn_off
    target: climate.wohnzimmer

This rule must not be duplicated in automations.

⚡ Energy rules

Energy policies may:

- avoid standby consumption
- correct extreme usage situations
- turn off devices in confirmed idle states

Energy policies must not:

- actively optimize comfort
- implement schedules
- interpret user intent

💡 Comfort boundaries

Governance may constrain comfort but does not orchestrate it.

Allowed:

- maximum temperature limits
- night brightness limits
- minimum temperature limits

Not allowed:

- activating scenes
- steering adaptive lighting (except for safety)
- implementing motion logic

🛑 What policies must never contain

- triggers
- delays (unless explicitly supported)
- sequences
- multi-step workflows
- intent interpretation
- user behavior logic

Policies are state rules, not programs.

🧪 Test and validation

When adding a new policy:

- verify entity mapping
- check conflicts with existing policies
- set the correct priority
- run a manual test scenario
- inspect logs

Only then use it in production.

🧠 Debugging

For unexpected behavior:

- inspect HA Governance logs
- identify the policy name
- compare priorities
- check triggering states
- distinguish automation vs policy

Rule of thumb:  
If something was turned off unexpectedly, it was probably Governance.

🔄 Change guidelines

Add a new policy only if:

- the rule is globally valid
- it appears multiple times in automations
- it describes a physical constraint
- it is safety or energy protection

Do not create policies for:

- one-off edge cases
- pure comfort features
- experimental logic

🎯 Target state

Governance should:

- be invisible in normal operation
- only intervene on boundary violations
- log clearly
- remain deterministic
- protect the Jarvis-style orchestrator

📌 Future

Governance is compatible with:

- goal-based optimization
- multi-room orchestrators
- LLM-assisted planning
- energy scoring

But it always remains the deterministic reality layer.
