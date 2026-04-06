# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs
2. Retrieval only
3. RAG (retrieval plus LLM)

Use clear, honest descriptions. It is fine if your system is imperfect.

---

## 1. System Overview

**What is DocuBot trying to do?**  
Describe the overall goal in 2 to 3 sentences.

> *DocuBot is meant to answer developer questions using a local set of project documentation. The goal is to make answers more reliable by retrieving relevant parts of the docs first instead of letting the model guess.*

**What inputs does DocuBot take?**  
For example: user question, docs in folder, environment variables.

> DocuBot takes a user question, the documentation files in the `docs/` folder, and an optional Gemini API key from the `.env` file for the modes that use the LLM.

**What outputs does DocuBot produce?**

> Depending on the mode, it returns either a direct LLM answer, raw retrieved snippets from the docs, or an answer generated from retrieved snippets. If it cannot find enough evidence, it returns a “I do not know” or fixed *refusal strings when there is no retrieval result or the model is instructed to refuse.*

---

## 2. Retrieval Design

**How does your retrieval system work?**  
Describe your choices for indexing and scoring.

- How do you turn documents into an index?
- How do you score relevance for a query?
- How do you choose top snippets?

> I changed retrieval so it works on smaller chunks instead of entire documents. The docs are split into paragraph-like sections, and the system builds an index based on the words that appear in each chunk. When a question comes in, it scores each chunk based on how much word overlap it has with the query, then returns the top matching snippets. For indexing, I lowercased the text and split it into tokens. For scoring, I used simple keyword overlap rather than anything advanced like embeddings and sorted the results by score and returned the highest scoring chunks for top snippets.

**What tradeoffs did you make?**  
For example: speed vs precision, simplicity vs accuracy.

> I kept the retrieval system simple on purpose. It is easier to understand and debug, but it is also more limited because it depends a lot on exact word matches. Splitting into smaller chunks improved precision, but it also means important details can sometimes get split across sections.

---

## 3. Use of the LLM (Gemini)

**When does DocuBot call the LLM and when does it not?**  
Briefly describe how each mode behaves.

- Naive LLM mode: It sends the full documentation corpus and the question to Gemini
- Retrieval only mode: It does not call the LLM at all. It only returns the retrieved snippets
- RAG mode: It first retrieves relevant snippets, then sends only those snippets to Gemini to generate an answer

**What instructions do you give the LLM to keep it grounded?**  
Summarize the rules from your prompt. For example: only use snippets, say "I do not know" when needed, cite files.

> In RAG mode, the model is told to answer using only the retrieved snippets and not make things up. If the snippets do not support an answer, it should say “I do not know based on the docs I have.” The prompt also tells it to mention which files the answer came from. In naive mode, it is also told to stay within the docs and say it does not know if the information is not there.

---

## 4. Experiments and Comparisons

Run the **same set of queries** in all three modes. Fill in the table with short notes.

You can reuse or adapt the queries from `dataset.py`.


| Query                                               | Naive LLM: helpful or harmful? | Retrieval only: helpful or harmful? | RAG: helpful or harmful? | Notes                                                                                                                                                                                                                                |
| --------------------------------------------------- | ------------------------------ | ----------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Example: Where is the auth token generated?         | Somewhat helpful but risky     | Helpful                             | Most helpful             | Naive mode can sound confident, but it may combine details from different files in a way that is not fully accurate. Retrieval only gives the evidence, while RAG gives a clearer answer based on that evidence.                     |
| Example: How do I connect to the database?          | Mixed                          | Helpful                             | Helpful                  | Naive mode gives a readable answer, but it can generalize beyond what the docs directly say.                                                                                                                                         |
| Example: Which endpoint lists all users?            | Mixed leaning helpful          | Helpful                             | Most helpful             | This is a more direct docs question, so naive mode is more likely to get close to the right answer because the information is stated clearly in the docs. It can still be vague since it does not clearly point to the exact source. |
| Example: How does a client refresh an access token? | Harmful overall                | Mixed                               | Mixed to helpful         | Naive mode is more likely to mix information about login and token refresh without making clear what the docs actually support.                                                                                                      |


**What patterns did you notice?**  

- When does naive LLM look impressive but untrustworthy?  
- When is retrieval only clearly better?  
- When is RAG clearly better than both?

> The naive LLM mode often looks the most convincing at first, but it is also the easiest to overtrust. Even when it sounds right, it can pull in details from different places or answer more broadly than the docs support. Retrieval only is often the most trustworthy because it shows the actual evidence, but it is not the easiest to use. You still have to read the returned snippets yourself and piece together the answer. RAG works best when retrieval is good. It gives a clearer answer than retrieval only, but it is still grounded in actual snippets. At the same time, if retrieval misses the right chunk, RAG can only work with what it was given.

---

## 5. Failure Cases and Guardrails

**Describe at least two concrete failure cases you observed.**  
For each one, say:

- What was the question?  
- What did the system do?  
- What should have happened instead?

> *Failure case 1:* In`SAMPLE_QUERIES`“How does a client refresh an access token?” In that case, retrieval sometimes pulled a snippet from the API reference instead of the more relevant explanation in the authentication docs. The system gave a partial answer, but it was missing useful context. Ideally, it should have retrieved the auth section first.

> *Failure case 2: Another failure case was when the question was too vague or not really covered by the docs. In those cases, naive mode could still give an answer that sounded reasonable even though the documentation did not actually support it. It should have refused instead of answering without enough evidence.*

**When should DocuBot say “I do not know based on the docs I have”?**  
Give at least two specific situations.

> *DocuBot should say that when retrieval does not return any meaningful snippets and when the returned snippets are too weak or incomplete to support a real answer. It should also say it when the question is outside the scope of the documentation.*

**What guardrails did you implement?**  
Examples: refusal rules, thresholds, limits on snippets, safe defaults.

> I changed retrieval so it returns smaller snippets instead of entire documents. I also added a threshold so the system does not answer when there is not enough evidence. In those cases, it refuses instead of returning random or weakly related context.

---

## 6. Limitations and Future Improvements

**Current limitations**  
List at least three limitations of your DocuBot system.

1. The retrieval system is based on simple keyword overlap, so it does not handle synonyms or meaning very well
2. Important information can get split across chunks, which sometimes weakens retrieval
3. RAG still depends completely on the quality of retrieval, so if the wrong snippets are selected, the final answer will also be weaker

**Future improvements**  
List two or three changes that would most improve reliability or usefulness.

1. Add better ranking so chunks from the most relevant document type are prioritized more consistently
2. Improve chunking by splitting based on headings or sections instead of only paragraph-style chunks
3. Use a stronger retrieval approach, such as embeddings or hybrid search

---

## 7. Responsible Use

**Where could this system cause real world harm if used carelessly?**  
Think about wrong answers, missing information, or over trusting the LLM.

> This system could cause problems if developers trust it too quickly, especially for security or database related questions. A wrong answer that sounds believable could lead to bad implementation decisions or cause someone to miss important details in the actual docs.

**What instructions would you give real developers who want to use DocuBot safely?**  
Write 2 to 4 short bullet points.

- Always verify important answers against the actual documentation files
- If the system refuses or seems uncertain, check the docs directly instead of pushing it to guess
- Treat RAG answers as summaries based on the retrieved snippets, not as something you should automatically trust without checking

---

