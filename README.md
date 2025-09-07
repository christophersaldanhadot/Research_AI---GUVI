🤖 AI Research Agent
An intelligent agent that automates web research by searching for information, extracting content from top sources, and generating structured, professional reports using Large Language Models. Built for the GUVI AI Hackathon.

✨ Key Features
Automated Web Search: Utilizes the SerpAPI to perform real-time Google searches on any topic.

Intelligent Content Extraction: Employs a robust, multi-layered approach using newspaper3k and BeautifulSoup to reliably extract content from websites, with graceful fallbacks.

Advanced AI Summarization: Feeds extracted content into Google's Gemini 1.5 Flash model to generate comprehensive reports with structured JSON output.

Professional Report Generation: Creates clean, readable reports featuring:

Highlighted Key Finding

Executive Summary

Detailed Analysis & Key Insights

Pros & Cons / Differing Viewpoints

APA 7th Edition Citations

Customizable Research: Fine-tune your research with filters for tone, publication date, region, and language.

Multiple Export Options: Download the final report as a clean Markdown file or a formatted PDF.

🛠️ Tech Stack
Frontend: Streamlit

Language: Python

LLM & AI: Google Gemini 1.5 Flash

Web Search: SerpAPI

Content Extraction: newspaper3k, BeautifulSoup4

PDF Generation: fpdf2

🚀 How to Run Locally
Clone the repository:

git clone [https://github.com/your-username/ai-research-agent.git](https://github.com/your-username/ai-research-agent.git)
cd ai-research-agent

Install dependencies:

Make sure you have a requirements.txt file. You can create one by running: pip freeze > requirements.txt

Then, install the necessary packages:

pip install -r requirements.txt

Set up your API keys:

Create a file named .env in the root directory.

Add your API keys to the file:

GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
SERPAPI_API_KEY="YOUR_SERPAPI_API_KEY"

Run the Streamlit app:

streamlit run AI_Researcher.py
s
