#%% Imports
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import nltk
import re
import collections
import multiprocessing
import csv
import string
import json


from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

#%% Get env

os.chdir(r"C:\Users\v-kirdwivedi\GitHub\SP_Perception")
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')


#%% Setting up OpenAI API

from openai import AzureOpenAI
import multiprocessing

client = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_KEY"),  
  api_version="2023-05-15"
)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6), retry_error_callback=lambda x: None)
def ask_GPT_backoff(content):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant but you only know how to use the words Yes and No."},
                  {"role":"system", "content":content}],
    )
    return response.choices[0].message.content

#%% Prompt Creation

def make_prompt(data_i):
    prompt = f'''
In a psychology experiment, participants played a game where they ranked four money prizes and received one of them.

Participants could maximize their earnings by ranking the prizes from highest-value to lowest-value. It is hard for participants to see exactly why this is the case. However, one intuitive reason why is that participants get a separate, independent chance to receive each prize, regardless of where they place the prize in their ranking, or at what stage the allocation process attempts to pair the participant and the prize.

At the end, participants filled out a reflection survey in which they were asked how they ranked the prizes and why.

The following lists the questions of the survey, along with one participant's response.


### Question: ### 
How did you typically rank the four prizes in the 10 real rounds? Please share with us your main considerations, even if you are not sure that you always thought about them all. 

### Participant’s response: ### 
{data_i[0]}


### Question: ### 
Did you change the way you rank throughout the game? If so, in which way and at which point? 

### Participant’s response: ### 
{data_i[1]}


### Question: ### 
In your view, did the explanations given during the game lead you to use a specific method of ranking the four prizes?

### Participant’s response: ### 
{data_i[2]}


### Question: ### 
If you answered “No” above: Why do you think the explanations did not lead you to use a specific method of ranking the four prizes?

### Participant’s response: ### 
{data_i[3]}


### Question: ### 
If you answered “Yes” above: What was that specific ranking method?

### Participant’s response: ### 
{data_i[4]}


### Questions for GPT: ###

Given the survey answers above, please answer the following two questions about this participant’s responses.
Please answer both of the following questions with simple "yes" or "no" answers.

1. Did the participant indicate that they ranked the prizes from highest-value to lowest-value?

    Example Answer: yes

2. If the answer to the above is "yes", did the participant give an accurate rationale, in terms of the obtainable prizes, for why playing this strategy would maximize their earnings?
    
    Example Answer: no
    
3. In particular, did they justify ranking the prizes from highest-value to lowest-value in terms of the important key principle: The prize a participant gets when they submit ranking R is always the highest that any ranking could get them, according to ranking R.

    Example Answer: yes

4. Alternatively, did they justify ranking the prizes from highest-value to lowest-value because it does not matter at what stage the allocation process attempts to pair the participant and the prize?

    Example Answer: no
'''
    return prompt

#%% Cleaning Response

def clean_response(response):
    ## Make lowercase
    response = response.lower()
    ## Remove punctuation
    response = response.translate(str.maketrans('', '', string.punctuation))
    ## Replace "\n" with " "
    response = response.replace("\n", " ")
    ## keep only words "yes" and "no"
    response = " ".join([word for word in response.split() if word in ["yes", "no"]])

    return response

#%% Batching

def run_batch_audit2(inputs_to_pool):
    ids, prompt_list = inputs_to_pool
    content = prompt_list
    response = ask_GPT_backoff(content)
    response = clean_response(response)
    zip_results = (ids, response)
    with open(f'results_3.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(zip_results)
    return zip_results

def parallel_process_audit(prompt_list):
        pool = multiprocessing.Pool(10)
        results = pool.map(run_batch_audit2, prompt_list)
        return results


# Define your function
def is_yes_or_no(input_string):
    if input_string.lower() in ["yes", "no"]:
        return True
    else:
        return False

# Define your schema
schema = {
    "Answer": {
        "type": "int",
        "description": "integer answer to the question",
        "required": ["Answer"]
    }
}

# Define your function object
function_object = {
    "name": "is_yes_or_no",
    "schema": schema
}

# Use the function in the chat completion
def ask_GPT(content):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant please use AnswerFormat function to format your response."},
            {"role":"system", "content":content}
        ],
        functions=[
            {
                "name": "AnswerFormat",
                "schema": schema
            }
        ],
        function_call="auto"
    )
    if response.choices[0].message.function_call is not None:
        json_response = json.loads(response.choices[0].message.function_call.arguments)
        print(f"Answer: {json_response}")
        return json_response
    else:
        # Print the text response if there is no function call
        print(response.choices[0].message.content)
        return None

# %% JSON_format
    
def ask_GPT_JSON(content, JSONSchema):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": f"Your are a helpful assistant that responds with a JSON object. Please use {JSONSchema} to format your response."},
            {"role":"user", "content":content}
        ])
    return response.choices[0].message.content

