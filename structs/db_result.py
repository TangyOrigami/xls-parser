from typing import Union
from structs.result import Result
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class DBResult:
    def __init__(self, result: Union[dict | tuple]):
        self.result = result

    @classmethod
    def parse(cls, raw_result: list[tuple, ...]):
        if len(raw_result) > 1:
            result = cls.create_hashmap(raw_result=raw_result)

        else:
            result = raw_result[0]

        return cls(result=result)

    @staticmethod
    def create_hashmap(raw_result: list[tuple, ...]) -> dict:
        result = {}

        for i in raw_result:
            result.update({i[0]: i[1]})

        return result
