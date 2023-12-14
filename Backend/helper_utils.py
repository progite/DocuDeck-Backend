import datetime

def extract_date(date: str):
    return datetime.datetime.strptime(date, "%Y-%m-%d")
    