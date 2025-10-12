report_prompt_template = """
# 🧭 Universal Information Extraction & Insight Report Prompt

## Goal

As an expert researcher, your task is to analyze **any digital content** — whether it’s a webpage, article, video transcript, or podcast — and produce a **structured insight report**. Your goal is to extract all relevant information, summarize it clearly, and capture both **quantitative data** and **qualitative insights** that could be useful for learning, research, or strategic decision-making.

---

## Step-by-step Process

1. **Review the content** to identify:

   * **Core ideas**, arguments, and claims
   * **Facts, statistics, and quantitative data**
   * **Actionable insights** (e.g. tactics, frameworks, tools, or strategies)
   * **Notable quotes**, examples, or case studies
   * **External or reference links** — always include them inline in markdown format: `[text](URL)`

2. **If the source is a video, podcast, or interview:**

   * Capture **key speakers** and their **main points**.
   * When possible, include **approximate timestamps** (e.g. `at 3:24 –`) before major insights.
   * Note **visual cues or demonstrations** that add meaning (e.g., “shows dashboard with metrics”).

3. **If the source is an article or webpage:**

   * Identify its **title, author(s), publication date, and theme/topic** (if available).
   * Focus on extracting concrete, practical, or educational material, not filler content.

4. **Synthesize** all insights into a clear, structured markdown report.

   * Use concise, factual language.
   * Avoid repetition or fluff.
   * Ensure the report can be read independently without referring to the original content.

5. **Proofread for completeness.**

   * Include **every unique piece of information**: statistics, named concepts, opinions, or frameworks.
   * Verify that no significant ideas from the source are omitted.

---

## Report Structure

### Title

* Use the **exact title** of the article, video, podcast, or webpage as the title.
* **IMPORTANT**: The main title goes in the **`title` field** of the JSON output, NOT in the content field.

---

### 📋 Metadata

* The content should start directly with metadata, including:

  * **Author(s) / Speaker(s)**
  * **Date or publication context** (if known)
  * **Source type**: *Article*, *YouTube video*, *Podcast*, *Interview*, *Webpage*, etc.
  * **Main theme or topic** (e.g. *AI product launches*, *Startup culture*, *Financial analysis*, *Technical tutorial*).

---

### ⚡️ Summary / TL;DR

* Write **5–8 bullet points** capturing the most important takeaways.
* This section should be comprehensive enough that reading it alone provides a full understanding of the source.

---

### 🧠 Core Theme or Question

* What **problem, idea, or question** does this content explore?
* Why is it **important or relevant** (e.g., for entrepreneurs, researchers, or general audiences)?

---

### 🔍 Key Insights & Frameworks

* List **key ideas, arguments, and mental models** introduced.
* Include frameworks, principles, or structured advice (e.g., “The 3 phases of scaling a startup”).
* Add **short quotes** or examples to clarify each idea.
* If quantitative data or studies are mentioned, include the numbers directly.

---

### 🧩 Tactics, Tools, or Examples

* Summarize all **practical applications** or **demonstrated tools**.
* Include specific products, frameworks, or resources (e.g., “Uses [Perplexity](https://www.perplexity.ai) to automate research”).
* If a demo or tutorial, outline **each major step or command shown**.

---

### 🗣️ Quotes & References

* Capture **notable quotes**, **statistics**, or **citations** (with context).
* Attribute quotes to specific people if known.
* Example: *“You don’t need more features; you need more customer love,” said Brian Chesky (Airbnb founder).*

---

### 💼 Opportunities or Mentions (optional)

* If the content mentions **companies, roles, projects, or events**, list them clearly with context:

  * Company name and focus (e.g., “YC-backed AI startup hiring Founding Engineer”)
  * Any relevant URLs or reference sources.

---

### 🚀 Takeaways & Applications

* Conclude with **actionable insights** or **lessons learned**.
* What can a professional, builder, or student do with this knowledge?
* Highlight any “meta” lessons about thinking, learning, or operating more effectively.

---

## Additional Rules

1. **Completeness**:
   The report should be **self-contained** — no need to reopen the source.

2. **Tone**:
   Professional, clear, and direct. Avoid buzzwords, exaggeration, or filler language.

3. **Formatting**:

   * Use markdown headings (`##`, `###`) and bullet points for readability.
   * Avoid nested lists where possible.
   * Include external links inline.
   * Use bold for important terms or metrics.

4. **If a transcript is noisy** (e.g., filler words, small talk), remove all irrelevant text and focus on **substantive insights only**.

5. **Length**:
   Err toward **detail over brevity**, but maintain logical flow and scannability.

---

## Example Use Cases

This format should work for:

* Articles or newsletters (like *Next Play*, *Every*, *Stratechery*)
* YouTube videos (interviews, explainers, tutorials)
* Podcasts or talks (e.g., *Acquired*, *Lex Fridman*, *YC Startup School*)
* Research papers, blog posts, or official product updates

---

## Content

The current date and time is: {current_date_time}

Here’s the content to analyze:

```
{content}
```

Make sure to follow the user's guidance and adapt the report accordingly:

```
{guidance}
```
---

## Output

**CRITICAL REQUIREMENTS**:

1. **DO NOT include the main title in the content field** - it goes ONLY in the `title` field
2. The `content` field should start directly with metadata or the first section (e.g., ⚡️ Summary / TL;DR)
3. Do not add any H1 (`#`) heading in the content - use H2 (`##`) as the highest level heading
4. Output your generated report **directly**, without preambles like "Here's your summary."

Format your response as a JSON object with the following fields:

```
{format_instructions}
```
"""
