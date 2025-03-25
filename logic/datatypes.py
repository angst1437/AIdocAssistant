from dataclasses import dataclass
from datetime import datetime

@dataclass
class TitleData:
    university_info: list
    work_type: str
    subject: str
    theme: str
    author: str
    group: str
    educator: str
    city: str
    year: str = str(datetime.today().year)

