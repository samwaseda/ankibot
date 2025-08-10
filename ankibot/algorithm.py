import yaml
import numpy as np
import pandas as pd


def load_data(file_path: str):
    with open(file_path) as f:
        data = yaml.safe_load(f)
    return pd.DataFrame(data["list"])


def get_options(df, p=None, n=4):
    if p is not None:
        p = 2.0 ** p
        p = p / np.sum(p)
    index = int(np.random.choice(np.arange(len(df)), p=p))
    choice = dict(df.iloc[index])
    options = [
        entry
        for entry in np.random.choice(
            df["answer"][df.group == choice["group"]], size=n, replace=False
        )
        if entry != choice["answer"]
    ]
    options = ([choice["answer"]] + options)[:n]
    np.random.shuffle(options)
    return index, choice, options


def correct(options: list[str], choice: dict[str, str], answer: int) -> bool:
    return options[answer] == choice["answer"]
