# MapleJourney Architecture Blueprint

## System Overview

**MapleJourney** is a **Sovereign Authority Platform** for Canadian immigration & settlement guidance. It combines:
- **RAG-Grounded LLM** (Claude Sonnet via Anthropic)
- **Live Web Search** (Omniscience Engine)
- **Persistent Memory** (Conversation history + profile context)
- **Credit-Based Access** (Free/Plus/Family tiers)

---

## Streaming Architecture: How "Maple" Responds

### 1. **Request Flow**
```
User Types Question
    ↓
POST /api/assistant/chat {message, session_id}
    ↓
[Authentication Check] ← JWT token from localStorage
    ↓
[Credit Check] ← If metered tier (free), debit credits
    ↓
[RAG Retrieval] ← Search official IRCC/legal documents
    ↓
[Memory Context] ← Load conversation history + user profile
    ↓
[Build System Prompt] ← Sovereign Authority instructions + Context
    ↓
[Stream Response] ← FastAPI StreamingResponse
    ↓
Browser receives: text/plain stream
    ↓
React component (useEffect) reads text chunks
    ↓
Real-time display: user sees response appearing word-by-word
```

### 2. **Backend Streaming (FastAPI)**

**File:** `backend/routers/chat.py`

```python
@router.post("/assistant/chat")
async def assistant_chat(body: ChatIn, user: dict = Depends(get_current_user)):
    """
    Returns StreamingResponse with chunks of text
    """
    async def gen():  # Generator function
        full = ""
        try:
            # 1. Call OpenAI/Anthropic API
            full = await _openai_chat_response(system, body.message)
            
            # 2. Attach citations from RAG
            full = attach_verified_citations_if_missing(full, rag_context)
            
            # 3. Enforce citation policy (must cite sources)
            full, compliant, reason = enforce_citation_policy(full)
            
            # 4. Add upsell nudge if credits low
            nudge = upsell_nudge(credit_balance, 0, tier)
            if nudge:
                full += nudge
            
            # 5. Store in conversation history
            await companion_memory.add_turn(
                session_id=session_id,
                user_id=uid,
                query=body.message,
                response=full,
            )
            
            yield full  # ← Send entire response as 1 chunk
            
        except Exception:
            yield grounded_fallback_response(reason="runtime-error")
    
    return StreamingResponse(
        gen(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
            "X-Maple-Credits": str(credit_balance),
        }
    )
```

### 3. **Frontend Streaming (React)**

**File:** `frontend/src/pages/app/Chat.jsx`

```javascript
const handleSendMessage = async () => {
    // 1. Call backend streaming endpoint
    const response = await fetch('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({ message, session_id }),
    });
    
    // 2. Get reader from response body stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = '';
    
    // 3. Read chunks as they arrive
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        accumulated += decoder.decode(value, { stream: true });
        
        // 4. Update UI in real-time (Framer Motion animates each chunk)
        setMessage(accumulated);
    }
};
```

---

## Key Components Breakdown

### **RAG (Retrieval Augmented Generation)**
- **Files:** `backend/services/rag.py`
- **Data:** Official IRCC docs, Immigration Act, provincial benefits
- **Flow:** User question → Search vector DB → Return top-5 citations → Include in system prompt
- **Result:** Every answer includes official sources + links

### **Companion Memory**
- **Files:** `backend/services/companion_memory.py`
- **Stores:** Conversation history, user profile context, memory embeddings
- **Purpose:** Claude can reference previous questions + user's situation
- **Persistence:** MongoDB collection `companion_messages`

### **Credit System**
- **Tiers:**
  - **Free:** 10 credits/day (1 simple Q = 1 credit, complex Q = 5-10 credits)
  - **Plus:** 150 credits/day unlimited
  - **Family:** Shared pool, all family members
- **File:** `backend/services/credits.py`
- **Logic:** Query classified by complexity → credits deducted before response streams

### **Citation Enforcement**
- **Rule:** Every legal claim MUST cite a source
- **Function:** `enforce_citation_policy()` checks response, rewrites if needed
- **Fallback:** If can't cite, returns grounded default response instead of hallucinated answer

---

## Data Model: Message Structure

### Chat Message (stored in DB)
```javascript
{
  _id: ObjectId(),
  user_id: "user@example.com",
  session_id: "unique-session-uuid",
  role: "user" | "assistant",
  content: "Long text of question or response",
  created_at: ISODate("2026-07-04T12:00:00Z"),
  
  // If role === "assistant":
  retrieved_docs: [
    { title: "...", url: "...", content: "..." }
  ],
  model_used: "claude-sonnet-4.6",
  credit_cost: 5,
  complexity: "simple" | "moderate" | "deep" | "research",
}
```

### Session (implicit - keyed by session_id)
- All messages with same `session_id` = 1 conversation
- User can have multiple concurrent sessions
- Sessions archived/purged based on tier retention policy (free = 30 days, paid = unlimited)

---

## New Features Integration: WhatsApp + iMessage

### **WhatsApp via Twilio**
- **Endpoint:** `POST /api/messaging/whatsapp/send`
- **Flow:** User types in WhatsApp → Twilio webhook → Forward to companion session → Stream response back via WhatsApp
- **Webhook:** `POST /api/messaging/whatsapp/webhook` (receive incoming messages)

### **iMessage via Firebase**
- **Endpoint:** `POST /api/messaging/push/send`
- **Flow:** User opts into push → Save device token → Send FCM push → Click opens app → Continues chat
- **iOS-native:** Apple APNs integration for native iMessage appearance

### **Unified Messaging Log**
```javascript
{
  _id: ObjectId(),
  user_id: "...",
  channel: "whatsapp" | "sms" | "push" | "web",
  direction: "inbound" | "outbound",
  content: "Message text",
  status: "sent" | "failed" | "delivered",
  timestamp: ISODate(),
}
```

---

## Streaming Headers

Every chat response includes metadata in HTTP headers:

```
X-Session-Id: 550e8400-e29b-41d4-a716-446655440000
X-Maple-Credits: 145
X-Maple-Cost: 5
X-Maple-Complexity: moderate
X-Maple-Limit: (if insufficient-credits)
```

Frontend uses these to:
- Update credit meter in real-time
- Display session ID for reference
- Show cost estimate before next question

---

## Performance Optimization

### **Streaming vs. Non-Streaming**
- **Streaming:** User sees response appearing word-by-word (better UX, faster perceived response)
- **Non-streaming:** User waits for entire response, then sees it all at once
- **MapleJourney:** Uses streaming for all chat responses

### **Chunk Size**
- Current: Sends entire response as 1 chunk (after LLM finishes)
- **Future:** Could chunk mid-generation if using streaming-enabled LLM (Anthropic Messages API supports this)

### **Caching**
- Headers: `Cache-Control: no-cache, X-Accel-Buffering: no`
- Prevents proxy/browser caching of stream
- Forces real-time delivery

---

## Deployment Implications

### **Local Dev**
- Backend: `127.0.0.1:8000` (uvicorn)
- Frontend: `192.168.1.82:3000` (webpack dev server)
- Streaming works over HTTP

### **Production (Railway/Render)**
- Need: Streaming-capable reverse proxy (nginx, Vercel, Railway all support)
- Auth: JWT in Authorization header (forwarded through streaming)
- Timeouts: Set high (600s+) for long-running LLM calls

### **Database (MongoDB)**
- Must support async driver (Motor)
- Chat messages indexed by `user_id`, `session_id`, `created_at`
- Companion memory indexed for fast retrieval during streaming

---

## What's Live Now

✅ **Working:**
- Chat endpoint with streaming response
- RAG retrieval from official documents
- Credit metering
- Session persistence
- Memory context + companion awareness

✅ **Ready to deploy:**
- WhatsApp integration (router created, awaiting Twilio keys)
- iMessage/push (Firebase integration, awaiting API keys)

🚀 **Next steps:**
1. Get Twilio API keys → activate WhatsApp
2. Set up Firebase project → enable iOS push
3. Update .env with keys
4. Restart backend
5. Deploy to Railway

---

## File Reference

| Component | File | Purpose |
|-----------|------|---------|
| **Chat API** | `backend/routers/chat.py` | Streaming endpoint + credit logic |
| **RAG Engine** | `backend/services/rag.py` | Document retrieval + citations |
| **Memory** | `backend/services/companion_memory.py` | Conversation persistence |
| **Credits** | `backend/services/credits.py` | Metering + wallet logic |
| **Messaging** | `backend/routers/messaging_channels.py` | WhatsApp + iMessage integration |
| **Frontend** | `frontend/src/pages/app/Chat.jsx` | React component + streaming UI |
| **Models** | `backend/models.py` | ChatIn, ChatOut data classes |

