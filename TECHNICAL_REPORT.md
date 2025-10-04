Technical Report: Gemini-Powered Hackathon Judge

1. Core Architecture and Tools
   The system is built as a Streamlit application using the LangChain framework to orchestrate
   interactions with the Google Gemini-2.5-Flash Large Language Model (LLM).
   Component Purpose Key Library/Tool
   User Interface Accepts project files,
   code, description,
   and custom judging
   criteria.
   streamlit
   LLM
   Integration
   Provides the
   intelligence for
   summarisation and
   judging.
   ChatGoogleGenerativeAI
   from langchain_google_genai
   Orchestration Manages the
   sequence of LLM
   calls (chains) and
   prompt engineering.
   LangChain
   PDF
   Extraction
   Reads and extracts
   text content from
   PDF technical
   reports.
   PdfReader from pypdf
   Video
   Encoding
   Converts the demo
   video file into a
   base64 string for
   LLM analysis.
   base64
2. Data Ingestion and Pre-Processing
   The system accepts the following inputs from the user:
3. Project Description and Code Snippet (raw text).
4. Technical Report (PDF or text file): Text content is extracted using PdfReader.
5. Demo Video (MP4 file): The video is read, encoded into a base64 string, and passed
   directly to the Gemini LLM via a HumanMessage with a 'media' part for initial
   summarisation.
6. Custom Judging Criteria: A configurable list of criteria and their percentage weights
   (which must sum to 100%).
7. The LangChain Pipeline (Two Stages)
   The core logic is structured into two sequential LangChain pipelines (or 'Chains'):
   Stage 1: Summarisation Chain
   ● Goal: To condense the raw technical report text and the LLM's initial video description
   into two distinct, focused summaries.
   ● Prompt Engineering: A dedicated SUMMARY_SYSTEM_PROMPT instructs the LLM to
   act as a "highly efficient text processor". It mandates the generation of a
   "TECHNICAL SUMMARY" (analysing architecture, feasibility, and impact) and a
   "PRESENTATION SUMMARY" (analysing presentation quality, clarity, and correctness).
   ● Process: This chain takes the extracted PDF text and the video description as input and
   produces a combined, structured text output of the two summaries.
   Stage 2: Judge Chain
   ● Goal: To analyse all submission components (description, code, and file summaries) and
   produce a detailed, quantitative scoring report.
   ● Prompt Engineering: A highly engineered GENERIC_JUDGE_SYSTEM_PROMPT is
   used. It enforces the persona of a
   "very strict judge" and dictates a multi-step process:
8. Analyse the Project Description, Summaries, and Code Snippet.
9. Score the project from 0 to 100 for each custom criterion.
10. Justify each score with a breakdown into up to five sub-criteria.
11. Calculate the final weighted score.
12. Strict Output Format: The prompt requires the final output to be in a specific
    Markdown format, including a placeholder [FINAL_CALCULATED_SCORE] that
    the LLM must replace with the exact numerical result of the weighted average.
    This ensures a consistent and machine-readable output.
    ● Process: This final chain generates the complete Hackathon Judge Report.
