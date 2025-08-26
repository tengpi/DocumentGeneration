replace the OPENAI_API_BASE and OPENAI_API_KEY by your own endpoint and key in the config file

adding DOUBAO LLM support and model selection in the config file

choose the llm provider, defauit is DOUBAO

score in the config file means if the judge agent give score less than it, it will trigger iteration with the judge's feedback until the score reaches it or the number of iteration reaches max_iteration

score should be between 0-5

run pdf_downloader_advanced.py to get the latest market news before summarization

run main_program.py to get the suggestions for customers

the input customer data is designated by INPUT_CUSTOMER_PROFILE_FILE in the config file, header line must be included

for the result for each customer:
    - A report in English will be generated
    - A report in Traditional Chinese in Cantonese tone will be generated
    - A reprot inculding the iteration and feedback from the judge agent will be generated for reference

