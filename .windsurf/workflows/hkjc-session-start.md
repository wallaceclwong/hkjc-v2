---
description: HKJC session start — load mempalace context before any work
---

## HKJC Session Start Protocol

Always run this at the start of every session involving the HKJC project.

### Step 1: Load palace overview
Call `mempalace_status` to get current wing/room inventory and protocol reminder.

### Step 2: Read diary
Call `mempalace_diary_read(agent_name="cascade", last_n=5)` to recall what happened in recent sessions.

### Step 3: Query project state
Call `mempalace_kg_query(entity="HKJC project")` and `mempalace_kg_query(entity="GCP Migration")` to verify current facts.

### Step 4: Before answering any question
Call `mempalace_search(query=<topic>)` or `mempalace_kg_query(entity=<entity>)` BEFORE responding. Never guess.

### Step 5: After session ends
Call `mempalace_diary_write(agent_name="cascade", entry=<AAAK summary>)` to record what was done.

### Step 6: When facts change
Call `mempalace_kg_invalidate(subject, predicate, object)` on old fact, then `mempalace_kg_add(...)` for new fact.
