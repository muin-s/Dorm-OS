from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db
from model import HostelExit

from .llm_engine import run_llm
from .prompt import build_prompt
from .risk import assess_risk
from .fee import calculate_fee
from .export import generate_exit_pdf

from datetime import datetime, date, timedelta

hostel_exit_bp = Blueprint("hostel_exit", __name__)


# ---------------- STUDENT CREATE ----------------
@hostel_exit_bp.post("/api/hostel-exit")
@jwt_required()
def create_exit():
    user_id = int(get_jwt_identity())

    data = request.get_json(silent=True) or request.form or {}
    text = (
        data.get("description")
        or data.get("text")
        or data.get("reason")
        or ""
    ).strip()

    if len(text) < 5:
        return jsonify({"error": "Please describe when you are leaving and returning."}), 400

    # ---- LLM CALL ----
    try:
        llm = run_llm(build_prompt(text))
        print("LLM PARSED =", llm)
    except Exception as e:
        print("LLM ERROR:", e)
        return jsonify({"error": "Could not understand the message"}), 400

    # ---- READ FIELDS ----
    leave_date = llm.get("leave_date")
    leave_time = llm.get("leave_time")
    return_date = llm.get("return_date")
    return_time = llm.get("return_time")
    room_type = llm.get("room_type", "unknown")

    # ---- APPLY DEFAULTS ----
    today = date.today().isoformat()

    if not leave_date:
        leave_date = today
    if not leave_time:
        leave_time = "09:00"
    if not return_date:
        return_date = leave_date
    if not return_time:
        return_time = "18:00"
    if not room_type:
        room_type = "unknown"

    # ---- BUILD DATETIME OBJECTS ----
    try:
        leave_dt = datetime.fromisoformat(f"{leave_date} {leave_time}")
        return_dt = datetime.fromisoformat(f"{return_date} {return_time}")
    except Exception as e:
        print("DATETIME ERROR:", e)
        return jsonify({"error": "Invalid date/time format from LLM"}), 500

    # ---- INTENT TYPE ----
    days = (return_dt.date() - leave_dt.date()).days
    exit_type = "REGULAR_EXIT" if days <= 1 else "HOSTEL_LEAVE"

    # ---- EMERGENCY CONTACT (optional later) ----
    emergency_contact = ""

    # ---- RISK + FEE ----
    risk = assess_risk(leave_dt, return_dt, emergency_contact)
    fee = calculate_fee(leave_dt, return_dt, room_type)

    # ---- SAVE ----
    entry = HostelExit(
        student_id=user_id,
        raw_input=text,
        exit_type=exit_type,
        leave_datetime=leave_dt,
        return_datetime=return_dt,
        room_type=room_type,
        emergency_contact=emergency_contact,
        risk_level=risk,
        calculated_fee=fee,
        status="pending"
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify({
        "ok": True,
        "parsed": llm,
        "exit_type": exit_type,
        "risk": risk,
        "fee": fee
    })


# ---------------- STUDENT HISTORY ----------------
@hostel_exit_bp.get("/api/hostel-exit/my")
@jwt_required()
def my_exits():
    user_id = int(get_jwt_identity())
    rows = HostelExit.query.filter_by(student_id=user_id) \
        .order_by(HostelExit.created_at.desc()).all()

    return jsonify([{
        "id": r.id,
        "exit_type": r.exit_type,
        "leave_datetime": r.leave_datetime.isoformat() if r.leave_datetime else None,
        "return_datetime": r.return_datetime.isoformat() if r.return_datetime else None,
        "risk_level": r.risk_level,
        "calculated_fee": r.calculated_fee,
        "status": r.status,
    } for r in rows])


# ---------------- ADMIN LIST ----------------
@hostel_exit_bp.get("/api/hostel-exit")
@jwt_required()
def list_all():
    if get_jwt().get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    rows = HostelExit.query.order_by(HostelExit.created_at.desc()).all()

    return jsonify([{
        "id": r.id,
        "student_id": r.student_id,
        "exit_type": r.exit_type,
        "leave_datetime": r.leave_datetime.isoformat() if r.leave_datetime else None,
        "return_datetime": r.return_datetime.isoformat() if r.return_datetime else None,
        "risk_level": r.risk_level,
        "calculated_fee": r.calculated_fee,
        "status": r.status,
    } for r in rows])


# ---------------- ADMIN APPROVE ----------------
@hostel_exit_bp.post("/api/hostel-exit/<int:id>/approve")
@jwt_required()
def approve(id):
    if get_jwt().get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    r = HostelExit.query.get_or_404(id)
    r.status = "approved"
    db.session.commit()
    return jsonify({"ok": True})


# ---------------- ADMIN REJECT ----------------
@hostel_exit_bp.post("/api/hostel-exit/<int:id>/reject")
@jwt_required()
def reject(id):
    if get_jwt().get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    r = HostelExit.query.get_or_404(id)
    r.status = "rejected"
    db.session.commit()
    return jsonify({"ok": True})


# ---------------- ADMIN PDF EXPORT ----------------
@hostel_exit_bp.get("/api/hostel-exit/export/pdf")
@jwt_required()
def export_exit_pdf():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403

    path = generate_exit_pdf()
    return send_file(path, as_attachment=True)
