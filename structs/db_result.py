from typing import Union
from structs.result import Result
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class DBResult:
    def __init__(self,  result: Result, data: Union[dict, None]):
        self.result = result
        self.data = data

    @classmethod
    def parse(cls, raw_result: list[tuple, ...]):
        log.info("raw_result: %s", raw_result)

        try:
            result, data = cls.create_dictionary(raw_result=raw_result)

        except Exception as e:
            log.error("Error parsing raw_result: %s", e)
            result = ERROR
            data = None

        finally:
            return cls(data=data, result=result)

    @staticmethod
    def create_dictionary(raw_result: list[tuple, ...]) -> dict:
        result = {}
        # [(id)] | [(first, middle, last)] | [(date, hours), ...]

        if len(raw_result) == 1:
            if len(raw_result[0]) <= 2:
                result.update({0: raw_result[0]})

            elif len(raw_result[0]) == 3:
                result.update(
                    {
                        0: raw_result[0][0],
                        1: raw_result[0][1],
                        2: raw_result[0][2]
                    }
                )

        else:
            for i in range(len(raw_result)):
                result.update(
                    {
                        i: ' '.join(' '.join(raw_result[i]).split())
                    }
                )

        return SUCCESS, result
