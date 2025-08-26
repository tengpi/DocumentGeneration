import glob
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import os, re
from datetime import datetime

from schema_parser import SchemaParser
from config_parser import get_config

from doubao_llm import DoubaoLLM
from openai_llm import OpenAILLM

# get config
config = get_config()
cfg = config.get_config()

# set environment variables for llm endpoint
config.set_environment_variables()

max_iterations = cfg.max_iterations
score_threshold = cfg.score
customer_file = cfg.input_customer_profile_file

# doubao_llm = DoubaoLLM()
if cfg.llm_provider.upper() == "DOUBAO":
    llm_provider = DoubaoLLM()
elif cfg.llm_provider.upper() == "OPENAI":
    llm_provider = OpenAILLM()
else:
    llm_provider = DoubaoLLM() # default to doubao


# Create the Summarization Agent
summarizer_agent = Agent(
    role='Wealth Management Report Generator',
    goal='Generate a structured, three-section output using provided customer data to assist Relationship Managers (RMs) in delivering personalized service & insights to each client through face-to-face meeting',
    backstory="""You are an expert wealth management advisor with years of experience in:
    - Customer profiling and behavioral analysis
    - Investment portfolio management and optimization
    - Market analysis and trend identification
    You excel at creating personalized, actionable insights for Relationship Managers.
    You are fluent in both Traditional Chinese (Cantonese tone) and British English.""",
    verbose=True,
    allow_delegation=False,
    llm=llm_provider
)

# Create the Judge Agent
judge_agent = Agent(
    role='Wealth Report Quality Assessor',
    goal='Evaluate the quality and completeness of wealth management reports',
    backstory="""You are a senior quality assessor specializing in wealth management reports.
    You evaluate reports based on:
    - Completeness of all three sections (Customer Profile, Wealth Portfolio, Market News)
    - Accuracy and relevance of insights
    - Professional presentation and formatting
    - Language quality (Traditional Chinese in Cantonese tone & British English)
    You rate reports on a scale of 1-5.""",
    verbose=True,
    allow_delegation=False,
    llm=llm_provider
)


def create_summary_task(customer_profile: str, market_news: str, feedback: str = None, previous_summary: str = None, iteration: int = 1):
    """Create a wealth management report generation task"""
    
    if iteration == 1:
        task_description = f"""Generate a comprehensive wealth management report for a Relationship Manager meeting.

Below is the customer profile
================================================================
{customer_profile}
================================================================

Below is the latest market news
================================================================
{market_news}
================================================================

IMPORTANT REQUIREMENTS:
1. Create THREE distinct sections: [Customer Profile], [Wealth Portfolio], [Market News]
2. Use bullet points for clarity
3. Write [Customer Profile], [Wealth Portfolio] and [Market News] in Traditional Chinese (Cantonese tone)
4. Keep content professional and actionable

Structure your output EXACTLY as follows:

[Customer Profile]
• [Analyse customer data and provide key insights]
• [Include actionable recommendations]

[Wealth Portfolio]
• [Personalised investment recommendations based on customer profile]
• [Asset allocation adjustment suggestions]
• [Portfolio optimisation opportunities]

[Market News]
• [Select 3 most relevant market news items]
• [Brief summary with relevance to customer]
• [Include actionable insights]

"""
    else:
        task_description = f"""You are on iteration {iteration} of improving the wealth management report.
        
Your previous report:
{previous_summary}

Judge's feedback:
{feedback}

Please create an improved report addressing the feedback while maintaining the three-section structure.

customer profile
================================================================
{customer_profile}
================================================================

latest market news
================================================================
{market_news}
================================================================

Remember to:
1. Maintain THREE sections: [Customer Profile], [Wealth Portfolio], [Market News]
2. Use bullet points
3. [Customer Profile], [Wealth Portfolio] and [Market News] in Traditional Chinese (Cantonese tone)
4. Address all feedback points"""

    return Task(
        description=task_description,
        expected_output="A complete three-section wealth management report with Customer Profile, Wealth Portfolio, and Market News sections",
        agent=summarizer_agent
    )


def create_judge_task(customer_profile: str, market_news: str, report: str, iteration: int = 1):
    """Create a judge task to evaluate the wealth management report"""
    return Task(
        description=f"""Evaluate this wealth management report (iteration {iteration}).

Check for:
1. THREE complete sections: [Customer Profile], [Wealth Portfolio], [Market News]
2. Customer Profile: Insightful analysis with actionable recommendations (in Traditional Chinese)
3. Wealth Portfolio: Personalized investment suggestions (in Traditional Chinese)
4. Market News: 3 relevant items with clear relevance to customer (in Traditional Chinese)
5. Professional formatting with bullet points
6. Language quality and appropriateness

The original content:
customer_profile:
================================================================
{customer_profile}
================================================================

market_news:
================================================================
{market_news}
================================================================

The report to evaluate:
{report}

Format your response as:
Score: [1-5]
Feedback: [Specific improvements needed if score < 5]

Score criteria:
5 = All sections complete, excellent insights, perfect language use
4 = All sections present, good insights, minor language issues
3 = Missing elements or weak insights
2 = Major omissions or poor quality
1 = Incomplete or unusable""",
        expected_output="Score and specific feedback",
        agent=judge_agent
    )


def translate_to_english(chinese_text: str) -> str:
    try:
        messages = [
            {"role": "system", "content": "You are a professional translator specializing in financial and wealth management content. "},
            {"role": "user", "content": f"Translate the following Traditional Chinese text to British English, maintaining the professional tone and all formatting (including bullet points and section headers).\n\n{chinese_text}"}
        ]
        # here we must use absolute model name
        # absolute_model_name = doubao_llm.model.split('/')[-1]

        model = llm_provider.model
        abolute_model_name = model.split('/')[-1] if '/' in model else model
        result = llm_provider.invoke(messages=messages, model=abolute_model_name)
        return result
        
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return "Translation failed. Original Chinese text preserved."
    

def iterative_summary_improvement(customer_identity: str, customer_profile: str, market_news: str):
    """Main function to iteratively improve wealth managenent reports"""
    iteration = 1
    score = 0
    feedback = None
    previous_summary = None

    # Save the original content
    timestamp = datetime.now().strftime("%Y%m%d_%H%M‰S")
    save_dir = f"outputs/{customer_identity}"
    iteration_filename = f"wealth_report_iterations_for_{customer_identity}_{timestamp}.txt"

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    with open(save_dir+'/'+iteration_filename, 'w', encoding='utf-g') as f:
        f.write("WEALTH MANAGEMENT REPORT GENERATION\n" )
        f.write("="*50 +"\n")
        f.write("Customer Data:\n")
        f.write(customer_profile)
        f.write("\n\n" )
    
    while score < score_threshold and iteration <= max_iterations:
        print(f"\n--- Iteration {iteration} ---")
        
        # Create summary task
        summary_task = create_summary_task(
            customer_profile=customer_profile,
            market_news=market_news,
            feedback=feedback,
            previous_summary=previous_summary,
            iteration=iteration
        )
        
        # Create crew for summarization
        summary_crew = Crew(
            agents=[summarizer_agent],
            tasks=[summary_task],
            process=Process.sequential,
            verbose=True
        )

        # Generate report
        summary_result = summary_crew.kickoff()
        summary = str(summary_result)

        # Clean thinking tags
        summary = re.sub(r'<think>.*?</think>','',summary, flags=re.DOTALL)
        summary = re.sub(r'<thinking>,*?</thinking>','',summary, flags=re.DOTALL)
        
        # Save current summary for next iteration
        previous_summary= summary
        
        # Create judge task
        judge_task= create_judge_task(customer_profile, market_news, summary, iteration)
        
        # Create crew for judging
        judge_crew = Crew(
            agents=[judge_agent],
            tasks=[judge_task],
            process=Process.sequential,
            verbose=True
        )

        # Evaluate report
        judge_result = judge_crew.kickoff()
        judge_output = str(judge_result)

        # Parse score and feedback
        try:
            score_line = [line for line in judge_output.split('\n')if 'Score:' in line][0]
            score = int(score_line.split(':')[1].strip().split()[0])
        except:
            score =1

        try:
            feedback_start = judge_output.find("Feedback:")
            if feedback_start != -1:
                feedback = judge_output[feedback_start + 9:].strip()
            else:
                feedback ="No specific feedback provided"
        except:
            feedback = "Error parsing feedback"

        # Save iteration result
        with open(save_dir+'/'+iteration_filename, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='* 50}\n")
            f.write(f"ITERATION {iteration} -Score: {score}/5\n" )
            f.write(f"{'=' * 50}\n")
            f.write(f"\nGenerated Report:\n{summary}\n")
            f.write(f"\nJudge Evaluation:\n{judge_output}\n")
        
        print(f"Score: {score}/5")

        if score >= 5:
            print("Perfect score achieved!")
            with open(save_dir+'/'+iteration_filename, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='* 50}\n")
                f.write("FINAL RESULT: Perfect score achieved!\n" )
                f.write(f"{'='* 50}\n")
                f.write(f"\nFINAL REPORT:\n{summary}\n")
        break

        iteration +=1

    if iteration > max_iterations:
        print(f"Maximum iterations({max_iterations}) reached.")
        with open(save_dir+'/'+iteration_filename, 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 50}\n" )
            f.write(f"FINAL RESULT: Maximum iterations reached. Final score: {score}/5\n")
            f.write(f"{'=' * 50}\n")
            f.write(f"\nFINAL REPORT:\n{summary}\n")

    print(f"\nAll results saved to: {save_dir+'/'+iteration_filename}")

    # save final result
    with open(f"{save_dir}/final report in traditional chinese {timestamp}.txt", encoding='utf-8') as f:
        f.write(f"{summary}\n")
    print(f"Traditional Chinese version saved to: {save_dir}/final report in traditional chinese {timestamp}.txt")

    # Translate and save English version
    print("Translating report to English...")
    english_summary=translate_to_english(summary)

    with open(f"{save_dir}/final_report_in_english_{timestamp},txt", 'w', encoding='utf-8') as f:
        f.write(f"{english_summary}n" )

    print(f"English version saved to: {save_dir}/final_report_in_english_{timestamp}.txt")

    return save_dir+'/'+iteration_filename, summary


def load_market_news(input_dir: str="input_docs")-> str:

    market_news_content = []

    supported_extensions = ['*.txt', '*.md']
    
    files_found = []
    for ext in supported_extensions:
        pattern = os.path.join(input_dir, ext)
        files_found.extend(glob.glob(pattern))

    if not files_found:
        print(f"Warning: No text files found in {input_dir}")
        return "No market news available."

    files_found.sort()

    for file_path in files_found:
        try:
            filename = os.path.basename(file_path)

            if filename.startswith('.') or filename == 'README.md':
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
                if content:
                    market_news_content.append(f"=== Source: {filename} ===")
                    market_news_content.append(content)
                    market_news_content.append("")

            print(f"Loaded: {filename}")
    
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            continue

    # merge all news
    if market_news_content:
        return "\n".join(market_news_content)
    else:
        return "No market news content found."
    
if __name__ == "__main__":
    # Load market news
    market_news = load_market_news()
    # with open('input_docs/market_news_latest.txt', 'r', encoding='utf-8') as f:
    #     market_news = f.read().strip()

    # Customer data (already parsed in the task)
    with open(customer_file)as f:
        header = f.readline().strip()# header
        for line in f:
            line = line.strip()
            if line:
                customer_profile = "\n".join([header, line])
                parser = SchemaParser("customer_data/data_schema.txt")
                formatted_customer_profile = parser.format_customer_data_section(customer_profile, False)
                # customer identity
                customer_identity = line.split(',')[0]
                # Run the iterative improvement process
                result_file, final_report = iterative_summary_improvement(customer_identity, formatted_customer_profile, market_news)
                print(f"nProcess completed, check '{result_file}' for all iteration results.")