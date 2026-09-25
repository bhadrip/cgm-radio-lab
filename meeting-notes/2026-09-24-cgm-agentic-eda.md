# CGM as a Test Vehicle for Agentic EDA

**Date:** September 24, 2026

**Participants:** Bhadri, Mohan

**Transcript:** [Granola meeting transcript](https://notes.granola.ai/t/be4e38d1-f7b2-4916-9e9d-0dceaae77d6a)

## Product opportunity

- A CGM-specific SoC was identified as the strongest product opportunity.
  - It would combine an electrochemical channel with a second optional channel.
  - It would be a deliberately small BLE-on-chip design.
- The full-stack CGM market is crowded, and Chinese competitors are difficult to beat.
  - FDA approval creates an additional barrier for US sales.
  - In Mohan's prior attempt at Synaptics, the team could not match EM Micro's power-consumption figures.
- CGM is the test case for validating the agentic EDA flow, not necessarily the eventual product.
- BLE channel sounding and ranging was discussed as another possible niche.
  - No current device appears to offer ranging alone; it is bundled with a full BLE stack.

## Chip-design process and opportunities for AI

- A tape-out takes approximately six to eight months across design and backend work.
  - Backend alone takes one to two months and two to three people.
  - Place-and-route remains human-driven.
  - The toolchain includes Synopsys and Cadence, with DRC and multiple verification stages.
- A 22 nm tape-out costs approximately $1 million, encouraging teams to include every plausible feature.
  - Shorter flows and lower NRE would make tightly scoped chips more viable.
  - The longer-term ambition is to reduce teams of roughly 200 people to 10–20 or fewer.
- RF is the hardest block because layout parasitics can cause failures that only become visible after tape-out.
  - Mohan described RF layout as “black magic” and “an art.”
  - MIT professor Kaushik Saxena is working on AI-enabled RFIC design, where generated structures have already exceeded human intuition.
- Pre-silicon AI tooling trails post-silicon tooling, largely because high tape-out costs make teams conservative.

## Agentic workflow demonstration

- Codex ran overnight on the CGM design, created pull requests, and ran simulations autonomously.
- It found an open-source EDA tool with a Docker image (not OpenROAD).
- Simulations ran inside Docker to keep results grounded and reduce hallucination risk.
- Prompting principles:
  - Work in small, vertical slices.
  - Do not hand-code; improve or tighten the specification and prompt instead.
  - Run three or four tasks in parallel and allow the agent to discover a suitable pattern.
  - Define success criteria up front, especially cost and power KPIs.
- Mohan reviewed the code comments, agreed that the flow made sense, and wants to take it further.
- Claude was recommended for Mohan's setup because he already has a subscription.

## Tooling and setup

- Bhadri is on the $200-per-month Codex plan, with 8% usage remaining and a reset on Saturday.
- Mohan is on the $20 plan and will likely need to upgrade.
- Docker is recommended for consistent execution across platforms; Mohan is using Windows.
- Mohan has been added as a GitHub collaborator, but Claude cannot connect to the repository.
  - Mohan will share the error message over WhatsApp so the permissions issue can be debugged asynchronously.
- Three research documents were generated overnight:
  - Market research
  - Agentic EDA landscape
  - Local verification methods
- Mohan will review the documents through Claude rather than reading them manually once GitHub access is working.

## Direction and ambition

- The core thesis is that domain expertise combined with an LLM may be enough to disrupt hardware design.
- Software is already being commoditized; hardware NRE and tape-out are the next frontier.
- Cadence and Synopsys are potential disruption targets. An open-source EDA stack with an MCP server could democratize access.
- The goal is tape-out-ready output with minimal human intervention for 80% of cases.
  - Humans remain in the loop primarily to approve or reject work.
  - Each person would spend approximately three to four hours per week while maximizing agent token usage.
- Mohan is open to starting a company in approximately one month if the direction becomes clearer.

## Action items

| Owner | Action | Notes |
| --- | --- | --- |
| Mohan | Set up Codex or Claude and replicate the agentic CGM flow. | Spend time over the weekend and define cost and power KPIs before starting. |
| Mohan | Share the GitHub/Claude connection error over WhatsApp. | Bhadri will debug the permissions issue asynchronously. |
| Mohan | Send the Kaushik Saxena AI-RFIC video and RF design book link. | The book covers RF layout craft; the video demonstrates AI-enabled RFIC work exceeding human intuition. |
| Mohan | Review the three agent-generated research documents through Claude. | Review the market, agentic EDA, and local-verification reports after GitHub access is fixed. |
