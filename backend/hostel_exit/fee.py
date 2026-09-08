def calculate_fee(leave_dt, return_dt, room_type):
    """
    Calculates mess/hostel refund for days absent.
    - Same day or 1 day leave: no refund
    - More than 1 day: refund for (total_days - 1) days
    - 2 seater: Rs 300/day refund
    - 4 seater or unknown: Rs 200/day refund
    """
    if not leave_dt or not return_dt:
        return 0

    total_days = (return_dt.date() - leave_dt.date()).days

    if total_days <= 1:
        return 0

    refund_days = total_days - 1

    if room_type == "2_seater":
        per_day = 300
    elif room_type == "4_seater":
        per_day = 200
    else:
        per_day = 150  # unknown room type gets base rate

    return refund_days * per_day
