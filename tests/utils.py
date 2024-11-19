def lines(text: str):
    return sorted(x.strip() for x in text.strip().split("\n"))
