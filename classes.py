from asyncio import create_task
from dataclasses import dataclass
from enum import Enum
from discord import ApplicationContext, Embed

class Mode(Enum):
    ticket = 1
    time = 2


@dataclass
class Ticket:
    date: str
    start: str
    end: str
    mode: Mode
    start_time: str
    end_time: str
    train_type: list[bool]
    train: list[str]

    def __post_init__(self):
        if self.mode == Mode.ticket:
            assert not self.start_time
            assert not self.end_time
            assert not self.train_type
            assert self.train
        elif self.mode == Mode.time:
            assert self.start_time
            assert self.end_time
            assert self.train_type
            assert not self.train
        else:
            raise ValueError("Invalid mode")

    @classmethod
    def from_embed(cls, embed: Embed):
        start_time = ""
        end_time = ""
        train_type = []
        train = []
        for field in embed.fields:
            if field.name == "日期":
                date = field.value.replace("-", "")
            elif field.name == "起點站":
                start = field.value
            elif field.name == "終點站":
                end = field.value
            elif field.name == "模式":
                mode = Mode.ticket if field.value == "車次" else Mode.time
            elif field.name == "開始時間":
                start_time = field.value
            elif field.name == "結束時間":
                end_time = field.value
            elif field.name == "車種":
                train_type = [0, 0, 0]
                if "新自強" in field.value:
                    train_type[0] = 1
                if "普悠瑪" in field.value:
                    train_type[1] = 1
                if "自強號" in field.value:
                    train_type[2] = 1
            elif field.name == "車次":
                train = field.value.split(" ")
        return cls(date, start, end, mode, start_time, end_time, train_type, train)

    def submit(self, ctx: ApplicationContext):
        from tra_spider import queryTicket
        create_task(queryTicket(ctx, self))
