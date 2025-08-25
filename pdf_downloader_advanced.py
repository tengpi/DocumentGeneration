import requests
import pdfplumber
import io
import os
from datetime import datetime
from typing import Optional, Tuple, List, Dict
import logging
import re
from crewai import Agent, Task, Crew

from config_parser import get_config

# Load configuration at program start
config = get_config()
cfg = config.get_config()

# Set environment variables
config.set_environment_variables()

class AdvancedPDFDownloader:
    """Advanced PDF download and text extraction utility class (using pdfplumber)"""

    def __init__(self, output_dir: str="downloaded_pdfs"):
        """
        Initialize PDF downloader

        Args:
            output_dir: Output directory path'
        """
        self.output_dir = output_dir
        self.logger = self._setup_logger()
        
        # Create output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"created output directory: {self.output_dir}")

    def _setup_logger(self)-> logging.Logger:
        """Set up logger"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger
    
    def download_pdf(self,url: str,timeout:int = 30)-> Optional[bytes]:
        """Download PDF file"""
        try:
            self.logger.info(f"Downloading PDF from: {url}")

            headers ={
                'user-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url,headers=headers, timeout=timeout)
            response.raise_for_status()

            self.logger.info(f"Successfully downloaded PDF, size: {len(response.content)} bytes")
            return response.content
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download PpF: {str(e)}" )
            return None
        
    def extract_text_from_pdf_advanced(self, pdf_content: bytes)-> Dict[str, any]:
        """
        Advanced text extraction using pdfplumber

        Returns:
            Dictionary containing text, tables, and other content
        """
        try:
            self.logger.info("Extracting content from PDF using pdfplumber" )

            pdf_file = io.BytesIO(pdf_content)
            extracted_content = {
                'text':[],
                'tables':[],
                'metadata':{}
            }

            with pdfplumber.open(pdf_file) as pdf:
                # Extract metadate
                extracted_content['metadata']= pdf.metadata
                
                # Iterate through each page
                for i, page in enumerate(pdf.pages):
                    page_content = {
                        'page': i + 1,
                        'text': '',
                        'tables': []
                    }

                    # Extract text
                    text = page.extract_text()
                    if text:
                        page_content['text']= text

                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        page_content['tables']= tables

                    extracted_content['text'].append(page_content)

                    # Store tables separately if available
                    if tables:
                        extracted_content['tables'].extend(tables)

            self.logger.info(f"successfully extracted content from {len(extracted_content['text'])} pages")
            return extracted_content
        
        except Exception as e:
            self.logger.error(f"Failed to extract content from PDF: {str(e)}")
            return {'text': [], 'tables': [], 'metadata':{}}
        
    def format_content(self, extracted_content: Dict[str, any])-> str:
        """
        Format extracted content into readable text

        Args:
            extracted_content; Dictionary of extracted content
        
        Returns:
            Formatted text
        """
        formatted_text =[]

        # Add metadata(if available)
        if extracted_content.get('metadata'):
            formatted_text.append("=== PDF Metadata ===" )
            for key,value in extracted_content['metadata'].items():
                if value:
                    formatted_text.append(f"{key}: {value}")
            formatted_text.append("")
        
        # Add content for each page
        for page_data in extracted_content.get('text', []):
            formatted_text.append(f"\n{'='*50}")
            formatted_text.append(f"Page {page_data['page']}")
            formatted_text.append('='*50)
           
            # Add text
            if page_data.get('text'):
               formatted_text.append(page_data['text'])

            # Add tables (if available)
            if page_data.get('tables'):
                for j, table in enumerate(page_data['tables']):
                    formatted_text.append(f"\n[Table {j+1}]")
                    for row in table:
                        # Filter None values and join cells
                        row_text =' | '.join(str(cell)if cell else ''for cell in row)
                        formatted_text.append(row_text)

        return '\n'.join(formatted_text)
    
    def clean_market_news_text(self,text: str)-> str:
        """
        Clean market news text, remove unnecessary content

        Args:
            text: Original text

        Returns:
            Cleaned text
        """
        # Remove extra blank lines
        text = re.sub(r'\n\s*\n','\n\n', text)

        # Remove repetitive headers/footers
        lines = text.split('\n')
        cleaned_lines =[]

        for line in lines:
            # Skip common header/footer patterns
            if any(pattern in line for pattern in ['Page', '免责声明', 'Disclaimer', '页码']):
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)
    
    def download_and_convert_advanced(self, url: str, output_filename: Optional[str] = None)-> Tuple[bool, str]:
        """
        Download PDF and convert to text file using advanced methods
        
        Args:
            url: PDF file URL
            output_filename: 0utput filename

        Returns:
            (Success flag, file path or error message)
        """
        # Generate output filename
        if output_filename is None:
            timestamp = datetime.now().strftime("'%Y%m%d_%H%M%S")
            output_filename = f"market_news_{timestamp}.txt"
        elif not output_filename.endswith('.txt'):
            output_filename += '.txt'

        # Download PDF
        pdf_content = self.download_pdf(url)
        if pdf_content is None:
            return False, "Failed to download PDF"

        # Extract content
        extracted_content =self.extract_text_from_pdf_advanced(pdf_content)
        if not extracted_content['text']:
            return False, "Failed to extract content from PDF"
        
        # Format content
        formatted_text= self.format_content(extracted_content)
        cleaned_text =self.clean_market_news_text(formatted_text)

        # Save text
        filepath = os.path.join(self.output_dir, output_filename)
        try:
            with open(filepath,'w',encoding='utf-8') as f:
                f.write(cleaned_text)
            self.logger.info(f"Text saved to: {filepath}")
            return True, filepath
        except Exception as e:
            return False,f"Failed to save text: {str(e)}"


def optimize_market_news_with_llm(raw_content: str)-> str:

    """
     Pptimize market news content using LLM

    Args:
         raw_content; Raw content extracted from PDF

    Returns:
        Optimized market news content
    """
    # Set LLM environment variables (if not already set)
    import os

    # Create optimization Agent
    optimizer_agent = Agent(
            role='Market News Content Optimizer',
            goal='0ptimize and format market news content for better readability',
            backstory="""You are an expert financial content editor specializing in:
            - Converting tables to readable text format
            - Removing redundant content
            - Organizing information in a clear, structured manner
            - Maintaining accuracy while improving readability
            You work with Traditional Chinese financial content.""",
            verbose=False,
            allow_delegation=False
        )

    # Create optimization task
    optimization_task = Task(
        description=f"""Please optimize the following market news content:
{raw_content[:5000]}  # Limit input length

Requirements:
1. Remove all metadata and page headers/footers
2. Convert any tables to descriptive text format(e.g.,"標普500指数收報6,370點, 下跌0.4%")
3. Organize content into clear sections
4. Remove duplicate information
5. Keep all important market data and insights
6. Use Traditional Chinese
7. Format numbers properly(e.g., use commas for thousands)
8. Convert bullet points to clear paragraphs where appropriate

Output a clean, well-structured market news report.""",
            expected_output="A clean, optimized market news report in Traditional Chinese.",
            agent=optimizer_agent
        )
        
    # Create Crew and execute
    crew = Crew(
            agents=[optimizer_agent],
            tasks=[optimization_task],
            verbose=False
        )

    try:
        result = crew.kickoff()
        # Clean thinking tags from result
        optimized_content =str(result)
        optimized_content = re.sub(r'<think>,*?</think>','',optimized_content, flags=re.DOTALL)
        optimized_content = re.sub(r'<thinking>,*?</thinking>','',optimized_content, flags=re.DOTALL)
        return optimized_content
    except Exception as e:
        print(f"Error optimizing content: {str(e)}")
        return raw_content #Return original content if optimization fails


def download_and_optimize_market_news()-> Tuple[bool, str]:
    """
    Download PDF, optimize content and save to input_docs directory

    Returns:
        (Success flag, file path or error message)
    """
    # Download PDF and extract content
    downloader = AdvancedPDFDownloader(output_dir="market_news")
    success,result = downloader.download_and_convert_advanced(
        "https://cms.hangseng.com/cms/ipd/chi/analyses/PDF/daily_chi.pdf"
    )

    if not success:
        return False, result
        
    # Read extracted content
    try:
        with open(result,'r',encoding='utf-8')as f:
            raw_content = f.read()
        
        print("optimizing content with LLM...")
        # Optimize content using LLM
        optimized_content = optimize_market_news_with_llm(raw_content)

        # Create input docs directory if it doesn't exist
        input_docs_dir ="input docs"
        if not os.path.exists(input_docs_dir):
            os.makedirs(input_docs_dir)

        # Save optimized content
        output_path = os.path.join(input_docs_dir, "market_news_latest.txt")
        with open(output_path, 'w',encoding='utf-8') as f:
            f.write(optimized_content)

        print(f"Optimized content saved to: {output_path}")
        return True, output_path

    except Exception as e:
        return False,f"Error processing content: {str(e)}"
    

# Function for integration with main program
def fetch_latest_market_news()-> str:
    """
    Get latest market news content

    Returns:
        Market news text content
    """
    # First try to &ead optimized content from input docs
    optimized_path ="input docs/market news_latest.txt"
    if os.path.exists(optimized_path):
        # Check if file is from today
        file_time = datetime.fromtimestamp(os.path.getmtime(optimized_path))
        if file_time.date() == datetime.now().date():
            with open(optimized_path, 'r',encoding='utf-8')as f:
                return f.read()

    # If not available or not from today, download and optimize new content
    success,result = download_and_optimize_market_news()
    if success:
        with open(result, 'r',encoding='utf-8') as f:
            return f.read()
    else:
        #Return default content
        return """市場新聞暫時無法獲取。請稍後再試。"""
    
    