import pandas as pd


def load_data(files: dict[str, str]) -> dict[str, pd.DataFrame]:
    data_dict = {}
    for data_name, file_path in files.items():
        try:
            df = pd.read_csv(file_path)
            data_dict[data_name] = df
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return data_dict