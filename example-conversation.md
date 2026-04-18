# Example Conversation

This example is designed to show what MemOS feels like when the retrieval layer is doing useful work instead of just dumping raw context.

## Conversation

**User:** I am building MemOS as a local-first memory layer for LLMs.  
**User:** !remember The forgetting engine is the most novel part and should stay visible in the UI.  
**User:** The dashboard should show a live graph, a retrieval panel, and a decay preview.

Later in the same session:

**User:** What should the assistant remember about this project?

## Retrieved context

```text
[MEMORY CONTEXT]
Use these memories if they improve the answer:
1. [PROJECT] I am building MemOS as a local-first memory layer for LLMs (importance=0.92, last_seen=0h ago)
2. [PREFERENCE] The forgetting engine is the most novel part and should stay visible in the UI (importance=0.84, last_seen=0h ago)
3. [FACT] The dashboard should show a live graph, a retrieval panel, and a decay preview (importance=0.77, last_seen=0h ago)
```

## Why this example works

- It mixes stable project facts with a design preference, which is exactly where conversational memory becomes more useful than plain document retrieval.
- The `!remember` message becomes a pinned memory, so the most strategic product choice remains available even after normal facts decay.
- The answer the LLM produces can now preserve intent, not just keywords.
