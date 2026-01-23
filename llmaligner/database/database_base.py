from pathlib import Path
from abc import ABC
from collections.abc import Iterator

DEFAULT_NUM_RESULTS = 10

class DatabaseBase(ABC):
    def __init__(self, path:Path | str):
        self.path = Path(path)
        self.load(self.path)

    @classmethod
    def build(
        self,
        conllu_path:Path,
        output_path:Path,
    ) -> "DatabaseBase":
        raise NotImplementedError()
    
    def load(
        self,
        path:Path | str,
    ):
        raise NotImplementedError()
    
    def __call__(
        self,
        query:str,
        k:int = DEFAULT_NUM_RESULTS,
    ) -> list[dict]:
        raise NotImplementedError()

    def __iter__(self) -> Iterator[dict]:
        raise NotImplementedError()
