import configparser

config = configparser.ConfigParser()
config.read("env.ini")

from langtrace_python_sdk import langtrace
langtrace.init(api_key = config["DEFAULT"]["LANGTRACE_API_KEY"])

from utils import load_data
from langchain_community.chat_models.ollama import ChatOllama
import boto3
from langchain_aws import ChatBedrock
from runner import Runner
from uuid import uuid4

LOCAL = True

file_paths = {
    "titanic": "data/titanic.csv",
}
data_dict = load_data(file_paths)

if LOCAL:
    llm = ChatOllama(model="llama3")
else:
    bedrock_rt = boto3.client(service_name="bedrock-runtime", region_name="ap-south-1")
    llm = ChatBedrock(model_id="meta.llama3-70b-instruct-v1:0")

runner = Runner(llm=llm, take_human_consent=False, debug_conversation=False, debug_final_state=False)

while True:
    question = input("Enter your question: (q to quit) ")
    if question == "q":
        break
    session_id = str(uuid4())
    ans = runner.run(data_dict, question, session_id)
    print("\n\n")