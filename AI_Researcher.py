import streamlit as st
import os
import google.generativeai as genai
from serpapi import GoogleSearch
import newspaper
from urllib.parse import urlparse
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🕵️‍♂️",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
    /* General styles */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    /* Title */
    h1 {
        font-size: 3rem;
        font-weight: 700;
    }
    /* Button */
    .stButton > button {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        border: 2px solid #4A4A4A;
        background-color: #1A1A1A;
        color: white;
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #FFFFFF;
        color: #000000;
        border: 2px solid #FFFFFF;
    }
    /* Text Input */
    .stTextInput > div > div > input {
        background-color: #1A1A1A;
        border-radius: 8px;
        border: 2px solid #4A4A4A;
        color: white;
    }
    /* Expander */
    .stExpander {
        border: 2px solid #4A4A4A !important;
        border-radius: 10px !important;
    }
    /* Sidebar */
    .css-1d391kg {
        background-color: #0A0A0A;
    }
    /* Highlight Box */
    .highlight-box {
        background-color: #1E1E1E;
        border-left: 5px solid #00A67D;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'AI Research Report', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        page_num = self.page_no()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f'Page {page_num} | Generated on {timestamp}', 0, 0, 'C')

def create_pdf(report_text: str, query: str) -> bytes:
    """Creates a PDF file from the markdown report text."""
    pdf = PDF()
    pdf.add_page()
    pdf.set_title(f"Research Report: {query}")
    pdf.set_font('Helvetica', '', 11)
    
    for line in report_text.split('\n'):
  
        if '<div class="highlight-box">' in line or '</div>' in line:
            continue
        
        cleaned_line = line.replace("✨ ", "").strip()
        line_for_pdf = cleaned_line.encode('latin-1', 'replace').decode('latin-1')

        if not line_for_pdf:
            pdf.ln(5) # Add a space for empty lines
            continue

        if line_for_pdf.startswith('# '):
            pdf.set_font('Helvetica', 'B', 18)
            pdf.multi_cell(w=0, h=10, text=line_for_pdf[2:].strip(), align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line_for_pdf.startswith('## '):
            pdf.set_font('Helvetica', 'B', 15)
            pdf.multi_cell(w=0, h=9, text=line_for_pdf[3:].strip(), align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line_for_pdf.startswith('### '):
            pdf.set_font('Helvetica', 'B', 13)
            pdf.multi_cell(w=0, h=8, text=line_for_pdf[4:].strip(), align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line_for_pdf.startswith('* '):
            pdf.set_font('Helvetica', '', 11)
            pdf.multi_cell(w=0, h=7, text=f'  * {line_for_pdf[2:].strip()}', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line_for_pdf.strip() == '---':
             pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
             pdf.ln(5)
        else:
            pdf.set_font('Helvetica', '', 11)
            pdf.multi_cell(w=0, h=7, text=line_for_pdf.strip(), align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    return bytes(pdf.output())

# --- API Key Configuration ---
GOOGLE_API_KEY = None
SERPAPI_API_KEY = None
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SERPAPI_API_KEY = st.secrets["SERPAPI_API_KEY"]
except (FileNotFoundError, KeyError):
    try:
        from dotenv import load_dotenv
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    except ImportError:
        pass 
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    
    pass


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "highlighted_finding": {"type": "string"},
        "executive_summary": {"type": "string"},
        "key_findings": {
            "type": "array",
            "items": {"type": "string"}
        },
        "detailed_analysis": {"type": "string"},
        "differing_viewpoints": {
            "type": "object",
            "properties": {
                "pros": {"type": "array", "items": {"type": "string"}},
                "cons": {"type": "array", "items": {"type": "string"}}
            }
        },
        "conclusion": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["executive_summary", "key_findings", "detailed_analysis", "conclusion", "citations"]
}


generation_config = {
    "temperature": 0.5,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
    "response_schema": RESPONSE_SCHEMA
}
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

MASTER_PROMPT = """
You are a world-class AI research analyst. Your task is to produce a high-quality, multi-faceted research report by populating a structured JSON object. Analyze the user's query and the provided web content to do this.

**Instructions:**
-   **Highlight:** First, identify the single most impactful, surprising, or recent finding from the content. Populate the 'highlighted_finding' field with this insight. It must be a concise, direct statement.
-   **Analyze:** Carefully analyze all provided content, which includes full article text and metadata. Synthesize information critically and objectively.
-   **Cite Rigorously:** For each point in 'key_findings', 'detailed_analysis', and 'differing_viewpoints', you MUST cite the source number in parentheses, like this: (Source 1).
-   **Format Citations:** Populate the 'citations' array with APA 7th Edition formatted citations for all sources. Use the provided metadata for this.
-   **Use Tables:** If the content allows for a direct comparison, embed a Markdown table within the 'detailed_analysis' string.
-   **Handle Viewpoints:** If pros and cons are not applicable, return empty arrays for them.
"""


def professional_extractor(link: str, snippet: str) -> tuple[str, list, str]:
    """
    Extracts content, authors, and publish date from a URL using a multi-layered approach.
    Layer 1: newspaper3k
    Layer 2: BeautifulSoup (as fallback)
    Layer 3: Search snippet (as final fallback)
    """
    try:
        
        article = newspaper.Article(link)
        article.download()
        article.parse()
        
        content = article.text
        authors = article.authors
        publish_date = article.publish_date.strftime('%Y-%m-%d') if article.publish_date else 'N/A'
        
        if len(content) < 250:
            raise ValueError("Content too short, trying BeautifulSoup.")
            
        return content, authors, publish_date

    except Exception as e:
        print(f"Newspaper3k failed for {link}: {e}. Falling back to BeautifulSoup.")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(link, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            main_content = soup.find('article') or soup.find('main') or soup.body
            paragraphs = main_content.find_all('p')
            content = ' '.join([p.get_text() for p in paragraphs])
            
            return content, [], 'N/A'
            
        except Exception as bs_e:
            print(f"BeautifulSoup also failed for {link}: {bs_e}. Using snippet.")
          
            return snippet, [], 'N/A'

def perform_research(query: str, time_filter: str, region: str, language: str):
    """Performs web search and extracts content from the top results."""
    params = {
        "q": query, "engine": "google", "api_key": SERPAPI_API_KEY,
        "gl": region, "hl": language,
    }
    if time_filter != 'any':
        params['tbs'] = f'qdr:{time_filter}'
    
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])
    if not organic_results:
        return "", []

    content_for_llm, source_metadata = [], []
    for i, result in enumerate(organic_results[:3]):
        source_num = i + 1
        link = result.get('link', 'N/A')
        title = result.get('title', 'N/A')
        snippet = result.get('snippet', '')
        
        metadata = {"title": title, "link": link, "domain": urlparse(link).netloc if link != 'N/A' else 'N/A'}
        
        content, authors, publish_date = professional_extractor(link, snippet)
        
        metadata.update({'authors': authors, 'publish_date': publish_date})
        source_metadata.append(metadata)

        content_for_llm.append(f"Source {source_num}:\nTitle: {title}\nLink: {link}\nAuthors: {', '.join(authors) if authors else 'N/A'}\nPublish Date: {publish_date}\nExtracted Content: {content}\n")
    return "\n---\n".join(content_for_llm), source_metadata

def generate_report(query: str, research_data: str, tone: str):
    """Generates a professional report by calling the Gemini API with a JSON schema."""
    toned_master_prompt = MASTER_PROMPT + f"\n**Tone Requirement:** The tone of the entire report must be **{tone}**."
    prompt_parts = [toned_master_prompt, f"**User Query:** {query}", "**Research Content:**", research_data]
    response = model.generate_content(prompt_parts)
    return json.loads(response.text)

def render_report_from_json(report_json: dict) -> str:
    """Converts the structured JSON report into a readable Markdown string."""
    md = []
    
    if report_json.get("highlighted_finding"):
        md.append("### ✨ Highlighted Finding")
        md.append(f'<div class="highlight-box">{report_json["highlighted_finding"]}</div>')

    if report_json.get("executive_summary"):
        md.append("## Executive Summary")
        md.append(report_json["executive_summary"])
        md.append("\n---\n")

    if report_json.get("key_findings"):
        md.append("## Key Findings")
        for finding in report_json["key_findings"]:
            md.append(f"* {finding}")
        md.append("\n---\n")

    if report_json.get("detailed_analysis"):
        md.append("## Detailed Analysis")
        md.append(report_json["detailed_analysis"])
        md.append("\n---\n")
    
    viewpoints = report_json.get("differing_viewpoints")
    if viewpoints and (viewpoints.get("pros") or viewpoints.get("cons")):
        md.append("## Pros & Cons / Differing Viewpoints")
        if viewpoints.get("pros"):
            md.append("### Pros")
            for pro in viewpoints["pros"]:
                md.append(f"* {pro}")
        if viewpoints.get("cons"):
            md.append("### Cons")
            for con in viewpoints["cons"]:
                md.append(f"* {con}")
        md.append("\n---\n")

    if report_json.get("conclusion"):
        md.append("## Conclusion")
        md.append(report_json["conclusion"])
        md.append("\n---\n")

    if report_json.get("citations"):
        md.append("## Citations (APA 7th Edition)")
        for citation in report_json["citations"]:
            md.append(f"* {citation}")

    return "\n".join(md)


st.title("AI Research Agent")
st.markdown("Your intelligent assistant for automated web research and analysis.")

with st.sidebar:
    st.header("🕵️‍♂️ Filter Search")
    tone = st.selectbox("Select Report Tone", ("Professional", "Simplified", "Academic", "Conversational"))
    
    st.header("🔍 Search Filters")
    time_filter_map = {"Any time": "any", "Past week": "w", "Past month": "m", "Past year": "y"}
    time_filter = st.selectbox("Publication Date", list(time_filter_map.keys()))
    time_filter_code = time_filter_map[time_filter]
    
    region_map = {"United States": "us", "India": "in", "United Kingdom": "uk", "Germany": "de", "Australia": "au"}
    region = st.selectbox("Search Region", list(region_map.keys()))
    region_code = region_map[region]
    
    language_map = {"English": "en", "German": "de", "French": "fr", "Spanish": "es"}
    language = st.selectbox("Search Language", list(language_map.keys()))
    language_code = language_map[language]

    with st.expander("About & Tech Stack", expanded=False):
        st.info("This AI Research Agent uses Google Gemini and SerpAPI to conduct automated research, synthesize findings, and generate professional reports.")
        st.markdown("""
        - **Frontend:** Streamlit
        - **LLM:** Google Gemini 1.5 Flash
        - **Search:** SerpAPI
        - **Extraction:** Newspaper3k & BeautifulSoup
        - **PDF Export:** FPDF
        """)

if 'report' not in st.session_state:
    st.session_state.report = None
if 'sources' not in st.session_state:
    st.session_state.sources = None

query = st.text_input("Enter your research topic:", placeholder="e.g., The impact of AI on renewable energy management", label_visibility="collapsed")

if st.button("Generate Report"):
    st.session_state.report = None
    st.session_state.sources = None
    if not query:
        st.error("Please enter a topic to research.")
    
    elif not SERPAPI_API_KEY or not GOOGLE_API_KEY:
        st.error("API keys are not configured. Please add them to your .env file or Streamlit secrets.")
    else:
        status = st.status("The agent is working...", expanded=True)
        try:
            status.update(label="Phase 1: Conducting web search...")
            research_data, sources = perform_research(query, time_filter_code, region_code, language_code)
            
            if not sources:
                status.update(label="Search complete.", state="complete")
                st.warning("Could not find relevant web pages with the selected filters. Please try a different query or broader filters.")
            else:
                status.update(label="Phase 2: Synthesizing findings...")
                report_json = generate_report(query, research_data, tone)
                report_md = render_report_from_json(report_json)
                st.session_state.report, st.session_state.sources = report_md, sources
                status.update(label="Report generation complete!", state="complete")
        except Exception as e:
            status.update(label="An error occurred.", state="error")
            st.error(f"An unexpected error occurred: {e}")

if st.session_state.report:
    st.markdown("---")
   
    st.markdown(st.session_state.report, unsafe_allow_html=True) 
    
    st.markdown("---")
    st.subheader("Export Report")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(label="⬇️ Download as Markdown", data=st.session_state.report, file_name=f"report_{query.replace(' ', '_').lower()}.md", mime="text/markdown")
    with col2:
        try:
            pdf_data = create_pdf(st.session_state.report, query)
            st.download_button(label="📄 Download as PDF", data=pdf_data, file_name=f"report_{query.replace(' ', '_').lower()}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Failed to generate PDF: {e}")

    with st.expander("View Source Details (Referenced in report as Source 1, Source 2, etc.)"):
        for i, source in enumerate(st.session_state.sources):
            st.write(f"**Source {i+1}: {source['title']}**")
            st.write(f"[{source['domain']}]({source['link']})")
            if 'authors' in source and source['authors']:
                st.write(f"  - **Authors:** {', '.join(source['authors'])}")
            if 'publish_date' in source and source['publish_date'] != 'N/A':
                st.write(f"  - **Published:** {source['publish_date']}")
else:
    st.info("Enter a research topic above and click 'Generate Report' to begin.")

