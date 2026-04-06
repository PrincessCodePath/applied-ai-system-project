# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**
  Sends the entire documentation corpus to a Gemini model and asks it to answer the question.
2. **Retrieval only mode**
  Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.
3. **RAG mode (Retrieval Augmented Generation)**
  Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.



## Reflection
DocuBot is meant to answer developer questions using a local set of project docs, but the bigger point is comparing what happens when a model tries to answer on its own, when it only retrieves evidence, and when it uses retrieval plus generation together. One thing that stood out to me was that even when naive mode sounded convincing, it was still capable of pulling details from different parts of the docs without clearly sticking to what actually answered the question. Retrieval only was often more trustworthy because it showed the evidence directly, but it was harder to use because the user still had to read and piece things together. RAG worked best when retrieval found the right snippets, which made it clear that better answers usually came from better system design, not just from using an LLM. I also think students could get tripped up by assuming retrieval is automatically more trustworthy, when simple keyword matching can still miss the best section or return something only partly helpful. Another place they may struggle is with guardrails, because it can feel like the system is failing when it says it does not know, even though that is actually the safer behavior. If I were helping students through this activity, I would have them compare the same exact question across all three modes and focus on what evidence each one is actually using. I would also remind them to trace the retrieval pipeline step by step instead of just trusting what the model suggests, because a lot of the learning here comes from understanding why the system behaves the way it does.

---

## Setup

### 1. Install Python dependencies

```
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example file:

```
cp .env.example .env
```

Then edit `.env` to include your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

```
python main.py
```

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

```
python evaluation.py
```

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
Implement or improve the retrieval index, scoring, and snippet selection.
- `llm_client.py`  
Adjust the prompts and behavior of LLM responses.
- `dataset.py`  
Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls

