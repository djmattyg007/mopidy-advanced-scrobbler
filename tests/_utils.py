from pathlib import Path


def path_to_data_dir(name):
    path = Path(__file__).parent / "data" / name
    return path.resolve()
