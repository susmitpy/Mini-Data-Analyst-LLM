INITIAL = """
You are a data scientist. Your task is to answer the given question. 
You have access to pandas dataframes using the 'data_dict' dictionary.

When you want to execute any code, write 'EXECUTE' followed by the Python code you want to run wrapped in triple backticks as shown below:
Be sure to store the output in a variable named 'result'. No need to write anything else in the message.

Here's a sample of the data you're working with:
{sample_data}

Based on the output in the 'result' variable, you can either:
1. Ask for more data by instructing EXECUTE again, or
2. Formulate an answer if you have sufficient information by typing 'END' followed by your final answer.

Example:
Message 1:
EXECUTE
```
result = data_dict['data']['col'].sum()
```

Message 2:
END The sum of the column is.

Note that in a single message both EXECUTE and END cannot be present. The answer should be concise and to the point. 
"""

QUESTION = "Question: {question}"
NO_CODE_FOUND = "No code found in the message. Please provide the code to execute."
CODE_ALREADY_EXECUTED_WITH_RESULT = "You have already asked to execute this code. The result was {result}. Use the result provided to formulate your answer."
IMPORTS_NOT_ALLOWED = "Import statements are not allowed. Refactor your code."
NO_RESULT_FOUND = "No result found. Please check the code."
EXECUTION_COMPLETE = "Execution complete. Output result: {result}"
ERROR_EXECUTING_CODE = "Error executing code: {e}"
BOTH_EXECUTE_END = "Both EXECUTE and END cannot be present in a single message. Please refactor your message."