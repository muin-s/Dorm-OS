import re
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
IST = ZoneInfo("Asia/Kolkata")

TIME_MAP = {
    "morning": "09:00", "afternoon": "15:00",
    "evening": "18:00", "night": "21:00",
    "midnight": "00:00", "noon": "12:00"
}

ROOM_MAP = {
    "2 seater": "2_seater", "2-seater": "2_seater", "two seater": "2_seater",
    "4 seater": "4_seater", "4-seater": "4_seater", "four seater": "4_seater"
}

WEEKDAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
MONTHS = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12,
    "january":1,"february":2,"march":3,"april":4,"june":6,
    "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
}

def extract_time(text: str) -> str:
    text = text.lower()
    for word, t in TIME_MAP.items():
        if word in text:
            return t
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text)
    if match:
        h = int(match.group(1))
        m = int(match.group(2) or 0)
        if match.group(3) == "pm" and h != 12:
            h += 12
        if match.group(3) == "am" and h == 12:
            h = 0
        return f"{h:02d}:{m:02d}"
    match24 = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match24:
        return f"{int(match24.group(1)):02d}:{match24.group(2)}"
    return None

def extract_room(text: str) -> str:
    text = text.lower()
    for k, v in ROOM_MAP.items():
        if k in text:
            return v
    return "2_seater"  # default 2 seater

def extract_duration_days(text: str) -> int:
    match = re.search(r"after\s+(\d+)\s+day", text.lower())
    if match:
        return int(match.group(1))
    match = re.search(r"for\s+(\d+)\s+day", text.lower())
    if match:
        return int(match.group(1))
    return 0

def extract_duration_hours(text: str) -> int:
    match = re.search(r"after\s+(\d+)\s+hour", text.lower())
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s+hour", text.lower())
    if match:
        return int(match.group(1))
    return 0

def parse_date_from_text(text: str, base: date) -> date:
    """Robust local date parser"""
    t = text.lower().strip()

    if "today" in t or "now" in t:
        return base
    if "day after tomorrow" in t:
        return base + timedelta(days=2)
    if "tomorrow" in t:
        return base + timedelta(days=1)

    # weekday like "sunday", "monday"
    for i, day in enumerate(WEEKDAYS):
        if day in t:
            current_dow = base.weekday()
            target_dow = i
            delta = (target_dow - current_dow) % 7
            if delta == 0:
                delta = 7
            return base + timedelta(days=delta)

    # "5 May", "May 5", "5th May"
    match = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS.keys()) + r")", t)
    if match:
        day = int(match.group(1))
        month = MONTHS[match.group(2)]
        year = base.year
        try:
            d = date(year, month, day)
            if d < base:
                d = date(year + 1, month, day)
            return d
        except:
            pass

    match = re.search(r"(" + "|".join(MONTHS.keys()) + r")\s+(\d{1,2})", t)
    if match:
        month = MONTHS[match.group(1)]
        day = int(match.group(2))
        year = base.year
        try:
            d = date(year, month, day)
            if d < base:
                d = date(year + 1, month, day)
            return d
        except:
            pass

    # DD/MM or DD-MM
    match = re.search(r"(\d{1,2})[/\-](\d{1,2})", t)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        year = base.year
        try:
            d = date(year, month, day)
            if d < base:
                d = date(year + 1, month, day)
            return d
        except:
            pass

    return None

def split_leave_return(text: str):
    text_lower = text.lower()
    for sep in ["and come back", "and return", "and will return",
                "and coming back", "will return", "come back",
                "returning on", "returning", "return on", "back on"]:
        if sep in text_lower:
            idx = text_lower.index(sep)
            return text[:idx], text[idx:]
    return text, ""

def run_llm(prompt_or_text: str) -> dict:
    now = datetime.now(IST)
    today = now.date()
    now_time = now.strftime("%H:%M")

    # Extract original user text from prompt
    match = re.search(r'"""(.+?)"""', prompt_or_text, re.DOTALL)
    text = match.group(1).strip() if match else prompt_or_text

    leave_part, return_part = split_leave_return(text)

    # ---- LEAVE ----
    leave_date = parse_date_from_text(leave_part, today) or today
    leave_time_str = extract_time(leave_part)
    if not leave_time_str:
        # if leaving today/now → use current time
        if leave_date == today:
            leave_time_str = now_time
        else:
            leave_time_str = "09:00"

    # ---- RETURN ----
    duration_days = extract_duration_days(text)
    duration_hours = extract_duration_hours(text)

    if duration_days > 0:
        return_date = leave_date + timedelta(days=duration_days)
        return_time_str = extract_time(return_part) or "18:00"
    elif duration_hours > 0:
        leave_dt_raw = datetime.combine(leave_date,
            datetime.strptime(leave_time_str, "%H:%M").time())
        return_dt_raw = leave_dt_raw + timedelta(hours=duration_hours)
        return_date = return_dt_raw.date()
        return_time_str = return_dt_raw.strftime("%H:%M")
    else:
        # check full text for day after tomorrow
        if "day after tomorrow" in text.lower():
            return_date = today + timedelta(days=2)
            return_time_str = extract_time(return_part) or "18:00"
        else:
            return_date = parse_date_from_text(return_part, today) if return_part else None
        return_time_str = extract_time(return_part) or "18:00"
        if not return_date:
            return_date = leave_date

    room_type = extract_room(text)

    result = {
        "leave_date": leave_date.isoformat(),
        "leave_time": leave_time_str,
        "return_date": return_date.isoformat(),
        "return_time": return_time_str,
        "room_type": room_type
    }
    print("LOCAL PARSER RESULT =", result)
    return result
