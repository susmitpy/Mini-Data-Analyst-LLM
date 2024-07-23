import pandas as pd
import re


def load_data(files: dict[str, str]) -> dict[str, pd.DataFrame]:
    data_dict = {}
    for data_name, file_path in files.items():
        try:
            df = pd.read_csv(file_path)
            data_dict[data_name] = df
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return data_dict

def get_executable_code_from_message(mssg: str) -> str:
    """
    EXECUTE
    ```
    {code}
    ```
    text

    OR

    EXECUTE
    ```python
    {code}
    ```
    text

    returns {code}

    """

    code = re.search(r"EXECUTE\s*```(?:python)?\s*(.*?)\s*```", mssg, re.DOTALL)
    if code:
        return code.group(1)
    raise Exception("No code found in message")