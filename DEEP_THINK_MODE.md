# Deep Think Mode - Multi-Agent Feature

**Single AI vs Multi-Agent Toggle** 🧠

---

## 🎯 **What is Deep Think Mode?**

Deep Think Mode enables the **Multi-Agent pipeline** for more thorough, accurate answers. By default, Brain-AI uses a **single AI** for fast responses. When you need higher quality, enable Deep Think!

---

## 🔄 **Two Modes Explained**

### **Fast Mode (Default)** ⚡

**Single AI** - Quick responses

```
User Question
    ↓
Vector Search
    ↓
Single LLM Call
    ↓
Answer (Fast!)
```

**Characteristics**:
- ✅ Fast response (~500-800ms)
- ✅ Lower cost (1 LLM call)
- ✅ Good for simple questions
- ✅ Sufficient for most queries

**Best for**:
- Factual lookups
- Simple questions
- Quick information retrieval
- When speed matters

---

### **Deep Think Mode** 🧠

**Multi-Agent** - Thorough, verified answers

```
User Question
    ↓
Vector Search
    ↓
Planner Agent (analyzes question)
    ↓
Solver 1 ┐
Solver 2 ├─ Generate 3 candidates (parallel)
Solver 3 ┘
    ↓
Verifier (optional tools: calculator, code sandbox)
    ↓
Judge (selects best answer)
    ↓
Answer (High Quality!)
```

**Characteristics**:
- ✅ Higher accuracy (multi-agent correction)
- ✅ Verified answers (calculator, code execution)
- ✅ Best answer selection (judge picks winner)
- ⏱️ Slower response (~1200-2000ms)
- 💰 Higher cost (5+ LLM calls)

**Best for**:
- Complex reasoning
- Math problems
- Code generation
- Critical decisions
- When accuracy matters most

---

## 🎨 **How to Use**

### **Method 1: Toggle Button (Header)**

Click the **"Deep Think"** button in the header:

```
┌─────────────────────────────────────┐
│  Brain-AI              [Deep Think] │  ← Click to toggle
│                        [Upload]     │
│                        [Settings]   │
└─────────────────────────────────────┘
```

**Visual States**:
- **OFF** (Fast Mode): Gray button, "Fast Mode" text
- **ON** (Deep Think): Purple/pink gradient, "Deep Think" text

---

### **Method 2: Settings Panel**

Open Settings and check the box:

```
Query Settings
┌─────────────────────────────────────┐
│ ☑ Deep Think Mode (Multi-Agent)    │  ← Toggle here
│ ☑ Enable Fuzzy Cache                │
│ ☑ Enable Verification               │
│ Confidence Threshold: 0.70          │
│ Fuzzy Threshold: 0.85               │
│ Top K Results: 5                    │
└─────────────────────────────────────┘
```

---

## 📊 **Performance Comparison**

### Example Question: "What is 15% of 250?"

#### **Fast Mode** ⚡
```
Time: 650ms
Process:
1. Vector search (50ms)
2. Single LLM call (600ms)
3. Answer: "37.5"

Accuracy: Good
Cost: 1 LLM call
```

#### **Deep Think Mode** 🧠
```
Time: 1,450ms
Process:
1. Vector search (50ms)
2. Planner (200ms)
3. 3 Solvers parallel (600ms)
4. Calculator verify (100ms)
5. Judge selection (500ms)
6. Answer: "37.5 (verified by calculator)"

Accuracy: Excellent (verified!)
Cost: 5 LLM calls
```

**Result**: Deep Think is 2.2x slower but provides verified accuracy!

---

## 🎯 **When to Use Each Mode**

### Use **Fast Mode** for:
- ✅ "What is the capital of France?"
- ✅ "Who wrote Romeo and Juliet?"
- ✅ "What does RAG stand for?"
- ✅ Simple factual lookups
- ✅ Quick information needs

### Use **Deep Think** for:
- 🧠 "Calculate the compound interest on $10,000 at 5% for 3 years"
- 🧠 "Write a Python function to sort a list using quicksort"
- 🧠 "Explain the proof of the Pythagorean theorem"
- 🧠 Complex reasoning tasks
- 🧠 Critical decisions

---

## 💡 **Technical Details**

### API Request Difference

**Fast Mode**:
```json
{
  "question": "What is the capital of France?",
  "top_k": 5,
  "enable_fuzzy_cache": true,
  "use_multi_agent": false  ← Single AI
}
```

**Deep Think Mode**:
```json
{
  "question": "Calculate 15% of 250",
  "top_k": 5,
  "enable_fuzzy_cache": true,
  "use_multi_agent": true  ← Multi-Agent!
}
```

---

### Backend Processing

**Fast Mode** (`use_multi_agent: false`):
```python
# Single LLM call
answer = llm.generate(
    prompt=f"Question: {question}\nContext: {context}",
    temperature=0.7
)
```

**Deep Think Mode** (`use_multi_agent: true`):
```python
# Multi-agent pipeline
plan = planner_agent(question, context)
candidates = [
    solver_agent(question, context, plan),
    solver_agent(question, context, plan),
    solver_agent(question, context, plan),
]
verified_candidates = [
    verify_answer(c, question) for c in candidates
]
best_answer = judge_agent(verified_candidates, question, context)
```

---

## 🎨 **UI Indicators**

### Button States

**Fast Mode (OFF)**:
```
┌─────────────────────┐
│ 🧠 Fast Mode        │  Gray background
└─────────────────────┘
```

**Deep Think (ON)**:
```
┌─────────────────────┐
│ 🧠 Deep Think       │  Purple/pink gradient
└─────────────────────┘
```

### Message Display

Messages show which mode was used:

**Fast Mode**:
```
┌─────────────────────────────────────┐
│ 🤖 Brain-AI                         │
│                                     │
│ Paris is the capital of France.     │
│                                     │
│ ✅ Confidence: 92%                  │
│ ⚡ Fast Mode                        │
│ ⏱️ 650ms                            │
└─────────────────────────────────────┘
```

**Deep Think Mode**:
```
┌─────────────────────────────────────┐
│ 🤖 Brain-AI                         │
│                                     │
│ 37.5 (verified by calculator)       │
│                                     │
│ ✅ Confidence: 98%                  │
│ 🧠 Deep Think (3 agents)            │
│ ✓ Verified                          │
│ ⏱️ 1,450ms                          │
└─────────────────────────────────────┘
```

---

## 📈 **Cost Analysis**

### LLM Call Costs (Example: DeepSeek)

**Fast Mode**:
- 1 LLM call per query
- Cost: ~$0.0001 per query
- 1,000 queries = $0.10

**Deep Think Mode**:
- 5 LLM calls per query (Planner + 3 Solvers + Judge)
- Cost: ~$0.0005 per query
- 1,000 queries = $0.50

**Recommendation**: Use Fast Mode by default, enable Deep Think only when needed!

---

## 🔧 **Configuration**

### Default Settings

```typescript
const [settings, setSettings] = useState({
  useMultiAgent: false,  // Fast Mode by default
  enableFuzzyCache: true,
  enableVerification: true,
  confidenceThreshold: 0.70,
  fuzzyThreshold: 0.85,
  topK: 5,
});
```

### Per-Query Override

You can toggle Deep Think on/off for individual queries without changing global settings!

---

## 🎯 **Best Practices**

### 1. **Start with Fast Mode**
Try Fast Mode first. If the answer isn't satisfactory, retry with Deep Think.

### 2. **Use Deep Think for Math**
Math problems benefit greatly from calculator verification.

### 3. **Use Deep Think for Code**
Code generation benefits from multi-agent review and sandbox testing.

### 4. **Monitor Costs**
Track your LLM usage. Deep Think uses 5x more calls.

### 5. **Cache Still Works!**
Both modes benefit from fuzzy caching. Cached answers are instant regardless of mode.

---

## 🚀 **Examples**

### Example 1: Simple Factual Question

**Question**: "What is the capital of France?"

**Fast Mode** ⚡:
```
Time: 580ms
Answer: "Paris is the capital of France."
Confidence: 95%
Cost: 1 call
```

**Deep Think** 🧠:
```
Time: 1,320ms
Answer: "Paris is the capital of France."
Confidence: 96%
Cost: 5 calls
```

**Verdict**: Fast Mode is sufficient! No need for Deep Think.

---

### Example 2: Math Problem

**Question**: "If I invest $5,000 at 6% annual interest compounded monthly for 5 years, how much will I have?"

**Fast Mode** ⚡:
```
Time: 720ms
Answer: "You'll have approximately $6,744.25"
Confidence: 78%
Verification: None
Cost: 1 call
```

**Deep Think** 🧠:
```
Time: 1,680ms
Answer: "You'll have $6,744.25"
Confidence: 99%
Verification: ✓ Calculator verified
Formula: A = P(1 + r/n)^(nt)
Cost: 5 calls
```

**Verdict**: Deep Think is better! Verified calculation with formula.

---

### Example 3: Code Generation

**Question**: "Write a Python function to check if a string is a palindrome"

**Fast Mode** ⚡:
```
Time: 950ms
Answer: 
def is_palindrome(s):
    return s == s[::-1]

Confidence: 85%
Verification: None
Cost: 1 call
```

**Deep Think** 🧠:
```
Time: 2,100ms
Answer:
def is_palindrome(s):
    # Remove spaces and convert to lowercase
    s = ''.join(s.split()).lower()
    return s == s[::-1]

# Tested with: "A man a plan a canal Panama"
# Result: True ✓

Confidence: 95%
Verification: ✓ Code executed successfully
Cost: 5 calls
```

**Verdict**: Deep Think is better! More robust with testing.

---

## 📊 **Statistics**

Track your usage:

```
Today's Stats:
┌─────────────────────────────────────┐
│ Total Queries: 47                   │
│ Fast Mode: 42 (89%)                 │
│ Deep Think: 5 (11%)                 │
│                                     │
│ Avg Response Time:                  │
│   Fast: 620ms                       │
│   Deep Think: 1,450ms               │
│                                     │
│ Cache Hit Rate: 68%                 │
│ LLM Calls: 67 (saved 31 via cache!) │
└─────────────────────────────────────┘
```

---

## 🎉 **Summary**

**Deep Think Mode gives you control!**

- 🚀 **Fast Mode**: Quick, efficient, good for most queries
- 🧠 **Deep Think**: Thorough, verified, best for complex tasks
- 🎛️ **Easy Toggle**: Switch anytime with one click
- 💰 **Cost Aware**: Use Deep Think only when needed
- ✅ **Both Benefit**: Fuzzy cache works with both modes

**Default**: Fast Mode (single AI)  
**When Needed**: Deep Think (multi-agent)  
**Result**: Best of both worlds! 🎯

---

**Version**: 4.5.0  
**Feature**: Deep Think Toggle  
**Status**: Production Ready  

🚀 **Enjoy intelligent AI with flexible thinking modes!** 🚀
