from datetime import datetime

def build_prompt(user_text: str):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return (
        "Understand the following message about hostel exit and return.\n\n"
        f"Current system date/time: {now}\n\n"
        "User message:\n"
        f"\"\"\"{user_text}\"\"\"\n\n"
        "You must extract structured information.\n\n"
        "The user may say things like:\n"
        "- I will leave today/tomorrow/on Monday/on 5 Feb\n"
        "- at 10am / evening / not mentioned\n"
        "- will return tomorrow/day after/on 12th / not mentioned\n"
        "- room type 2 seater / 4 seater / not mentioned\n\n"
        "Some details may be missing — handle defaults.\n\n"
        "Default rules to apply:\n"
        "- if leave date missing → use today's date\n"
        "- if leave time missing → use 09:00\n"
        "- if return date missing → same as leave date\n"
        "- if return time missing → 18:00\n"
        "- if room type missing → \"unknown\"\n\n"
        "Relative word meanings:\n"
        "- today = current date\n"
        "- tomorrow = +1 day\n"
        "- day after tomorrow = +2 days\n"
        "- morning = 09:00\n"
        "- afternoon = 15:00\n"
        "- evening = 18:00\n"
        "- night = 21:00\n\n"
        "Convert everything to:\n"
        "- date format YYYY-MM-DD\n"
        "- time format HH:MM (24-hour)\n\n"
        "Return ONLY this JSON object with no explanation:\n"
        "{{\n"
        " \"leave_date\": \"YYYY-MM-DD\",\n"
        " \"leave_time\": \"HH:MM\",\n"
        " \"return_date\": \"YYYY-MM-DD\",\n"
        " \"return_time\": \"HH:MM\",\n"
        " \"room_type\": \"2_seater\" | \"4_seater\" | \"unknown\"\n"
        "}}\n"
    )
