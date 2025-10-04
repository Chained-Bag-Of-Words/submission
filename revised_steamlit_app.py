import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pypdf import PdfReader
from langchain_core.messages import HumanMessage
import base64



# Set API keys in your environment
# os.environ["GOOGLE_API_KEY"] = "Google API KEY"
# os.environ["LANGCHAIN_API_KEY"] = "Langchain API KEY"
# os.environ["LANGCHAIN_TRACING_V2"] = "true"  <--- set it to true

DEFAULT_CRITERIA = [
    {"Criterion": "Originality", "Weight (%)": 30},
    {"Criterion": "Technical Feasibility", "Weight (%)": 25},
    {"Criterion": "Impact", "Weight (%)": 20},
    {"Criterion": "Presentation Quality", "Weight (%)": 15},
    {"Criterion": "Code Quality & Correctness", "Weight (%)": 10},
]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2  # Low temperature for predictable results
)

output_parser = StrOutputParser()

SUMMARY_SYSTEM_PROMPT = """
You are a highly efficient text processor. Your task is to analyze raw content from technical documentation and presentation notes to generate focused summaries.

**INSTRUCTIONS:**
1. **Technical Content Summary:** Read the provided technical documentation text. Summarize its key points regarding technical architecture, feasibility, and impact. If the content is empty or short, state "No technical content provided for analysis." Label this section clearly as "TECHNICAL SUMMARY:".
2. **Presentation Summary:** Read the provided presentation notes or summary if its a complete presentation video. Summarize the overall quality of the presentation, focusing on the clarity , feasibility , if the technicalities stated are correct or not, has it been plagiarised and is the content accurate. If the summary is empty or short, state "No presentation notes provided for analysis." Label this section clearly as "PRESENTATION SUMMARY:"
else-> if it is a video of the project in working then judge and base your summary on if the project works and if everything is correct, both cases are equally desirable so grade them accordingly

Combine both summaries into a single, cohesive output. Do not include any other commentary.
"""

SUMMARY_USER_PROMPT = """
---
TECHNICAL DOCUMENT TEXT (from PDF/Report, length: {pdf_length} characters):
{pdf_text_content}
---
DEMO VIDEO SUMMARY (from video, length: {presentation_length} characters):
{presentation_summary}
---
Generate the summaries based on the system instructions.
"""

summary_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SUMMARY_SYSTEM_PROMPT),
        ("user", SUMMARY_USER_PROMPT)
    ]
)

summary_chain = summary_prompt | llm | output_parser





GENERIC_JUDGE_SYSTEM_PROMPT = """
You are an experienced, world-class very strict judge for a major hackathon. Your task is to analyze a project submission and provide a fair, detailed, and quantitative score out of 100.
you should judge the data provided for accuracy , details and completeness.
No marks for effort only give marks for the results they got.

**JUDGING CRITERIA & WEIGHTS:**
{criteria_list}

**PROCESS:**
1.  **Analyze** the provided Project Description, Pre-generated Summaries (Technical and Presentation), and Demo Code Snippet, .
2.  **Score** the project from 0 to 100 for EACH of the defined criteria.
3.  **Justify** each score with detailed breakdown in sub caetgories with accurate description of the technical aspects(do not givve scores in sub categories but justify the main score with sub criterion).
4.  **Calculate** the Final Weighted Score out of 100 based on the individual scores and the corresponding weights.
5.  **CRITICAL:** Replace the placeholder `[FINAL_CALCULATED_SCORE]` with the exact numerical result of the weighted average calculation (e.g., 85.5, 72.0).

**REQUIRED OUTPUT FORMAT (Markdown):**

# Hackathon Judge Report

## Final Weighted Score: [FINAL_CALCULATED_SCORE]/100.0

## Detailed Category Scores & Analysis
##the presentation summary could be a presentation or a demo video summary,then score it based on if the project is working in the demo video summary and the ccriterion below , and if its a presentation summary then rate it based on criterias below.
##in the below categories, analyse in multiple sub-criterias and breakdown the score in relevent sub categories(do not givve scores in sub categories but justify the main score with sub criterion).
## keep sub criteria breakdown up to 5 criterion
## For code completeness and correctness, if the issue is very minor and easily fixable do not reduce marks heavily, if the issue is architectural or the code is not functional reduce marks heavily
{category_scores}



## Judge's Summary
[Provide a final, accurate summary of the project's strengths and one area for improvement.]
[If the project fails horribly in one or more than one categories(a 0 score) , state next to the final score that this project has failed]
"""



JUDGE_USER_PROMPT = """
Please judge the following hackathon submission using the summaries generated from the files.

**SUBMISSION DETAILS**

---
**Project Description:**
{description}

---
**FILE SUMMARIES (Generated by Pre-Chain):**
{file_summaries}
---
**Demo Code Text:**

{code_text}

"""

st.set_page_config(
    page_title="AI-Based Hackathon Judge",
    layout="wide",
    #initial_sidebar_state="expanded"
)

st.title("🏆 Gemini-Powered Hackathon Judge")
st.markdown("Upload files and text. A **Summarization Chain** processes the files into text, which is then passed to the **Judge Chain** for scoring.")



# --------- Submission Input Section ---------

st.header("Project Submission Details")
col1, col2 = st.columns(2,vertical_alignment="top")
with col1:
    st.text("\n")
    description = st.text_area(
        "📝 Project Description (Concept & Goal) [Required]",
        height=200,
        placeholder="e.g., A multi-user collaborative drawing board built with React and Firestore for real-time art sessions.",
        key="desc"
    )
    code_text = st.text_area(
        "💻 Demo Code Snippet (Key files or core logic) [Required]",
        height=300,
        placeholder="Paste a relevant code snippet here (e.g., the main logic or data handling files).",
        key="code"
    )
with col2:
    
    #st.sidebar.markdown("Edit the criteria and ensure the **Total Weight sums to 100%**.")
    st.markdown("⚖️ Define Judging Criteria & Weights")

    edited_criteria = st.data_editor(
        #"⚖️ Define Judging Criteria & Weights",
        DEFAULT_CRITERIA,
        column_config={
            "Criterion": st.column_config.TextColumn("Criterion Name", required=True),
            "Weight (%)": st.column_config.NumberColumn("Weight (%)", min_value=1, max_value=100, required=True),
        },
        #disabled=["Criterion"],
        num_rows="dynamic",
        hide_index=True,
        key="criteria_editor"
    )
    pdf_file = st.file_uploader(
        "📄 Upload Technical Report (PDF or Text File) [Required]", 
        type=['pdf', 'txt'], 
        key="pdf_upload"
    )
    demo_video = st.file_uploader(
        "🎬 Upload Demo Video (MP4 only) [Optional but recommended]",
        type=['mp4'],
        key="demo_video"
    )

judge_button = st.button("⚖️ Generate Judge's Score & Report", type="primary")

# --------- Gemini YouTube Summary Handling ---------



if judge_button and description and code_text and pdf_file and demo_video:
    
    
    # video_file_path = demo_video.path
    with st.spinner("Generating demo video summary..."):

        video_mime_type = "video/mp4"
        # with open(video_file_path, "rb") as video_file:
        encoded_video = base64.b64encode(demo_video.read()).decode('utf-8')

        message = HumanMessage(
            content=[
                {"type": "text", "text": "Describe what's happening in this video."},
                {"type": "media", "data": encoded_video, "mime_type": video_mime_type}
            ]
        )
        video_response = llm.invoke([message])


    

    # 1. Extract PDF or text content
    pdf_text_content = ""
    if pdf_file.name.endswith(".pdf"):
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                pdf_text_content += page_text
    else:
        # it's a .txt file
        pdf_text_content = pdf_file.read().decode("utf-8")
    if not pdf_text_content.strip():
        st.warning("The uploaded document appears to be empty or unreadable.")
        pdf_text_content = "The uploaded document was empty or contained no readable text."

    # 2. Handle YouTube summary or mark blank
    presentation_summary = ""
    presentation_summary = video_response.text()

    # 3. Check criteria weights
    total_weight = sum(item["Weight (%)"] for item in edited_criteria)
    if total_weight != 100:
        st.error(f"Error: The total weight of all criteria must sum up to 100%. Current sum: {total_weight}%.")
        st.stop()

    dynamic_criteria = {
        item["Criterion"]: item["Weight (%)"] / 100.0
        for item in edited_criteria
    }
    criteria_markdown = "\n".join(
        [f"- {k}: {v*100:.0f}%" for k, v in dynamic_criteria.items()]
    )

    category_scores_prompt = ""
    for criterion, weight in dynamic_criteria.items():
        category_scores_prompt += f"""
### {criterion} (Weight: {weight*100:.0f}%)
**Score:** [0-100]/100
**Justification:** [Your analysis here]
"""

    final_judge_system_prompt = GENERIC_JUDGE_SYSTEM_PROMPT.format(
        criteria_list=criteria_markdown,
        category_scores=category_scores_prompt.strip()
    )

    # Create judge chain dynamically
    dynamic_judge_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", final_judge_system_prompt),
            ("user", JUDGE_USER_PROMPT)
        ]
    )
    judge_chain = dynamic_judge_prompt | llm | output_parser

    # 4. Summarization stage
    with st.spinner("Stage 1: Running Summarization Chain (Analyzing PDF and Video summary)..."):
        try:
            summary_inputs = {
                'pdf_text_content': pdf_text_content,
                'presentation_summary': presentation_summary,
                'pdf_length': len(pdf_text_content),
                'presentation_length': len(presentation_summary)
            }
            response = summary_chain.invoke(summary_inputs)
            file_summaries = response.content if hasattr(response, "content") else str(response)

            st.markdown("---")
            st.subheader("✅ Summarization Chain Output ")
            st.code(file_summaries, language='markdown')
            st.markdown("---")
        except Exception as e:
            st.error(f"An error occurred during the Summarization Chain: {e}")
            st.stop()

    # 5. Judging stage
    with st.spinner("Stage 2: Running Judge Chain (Scoring Project)..."):
        try:
            judge_inputs = {
                'description': description,
                'file_summaries': file_summaries,
                'code_text': code_text
            }
            judging_report = judge_chain.invoke(judge_inputs)
            st.header("Judge's Official Report")
            st.markdown(judging_report)
        except Exception as e:
            st.error(f"An error occurred during the Judging Chain: {e}")

elif judge_button:
    st.error("Please fill in the Project Description, Code Snippet, upload a Technical Report, and ensure your criteria weights sum up to 100% in the sidebar.")
