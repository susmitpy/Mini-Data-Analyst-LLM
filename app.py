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
    "titanic_train": "data/titanic_train.csv",
    "titanic_test": "data/titanic_test.csv",
}
data_dict = load_data(file_paths)

TEMPERATURE = 0.1
if LOCAL:
    llm = ChatOllama(model="llama3", temperature=TEMPERATURE)
else:
    bedrock_rt = boto3.client(service_name="bedrock-runtime", region_name="ap-south-1")
    llm = ChatBedrock(model_id="meta.llama3-70b-instruct-v1:0",model_kwargs=dict(temperature=TEMPERATURE))

runner = Runner(llm=llm, take_human_consent=False, debug_conversation=False, debug_final_state=False)

while True:
    question = input("Enter your question: (q to quit) ")
    if question == "q":
        break
    session_id = str(uuid4())
    ans = runner.run(data_dict, question, session_id)
    print("\n\n")