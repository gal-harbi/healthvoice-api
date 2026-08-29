import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# הגדרת Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("HealthVoiceClinic")

app = FastAPI(title="HealthVoice Clinic System")

# Data Models
class AuthRequest(BaseModel):
    id_number: Optional[str] = None

class SlotRequest(BaseModel):
    doctor_id: Optional[str] = None
    specialty: Optional[str] = None
    doctor_name: Optional[str] = None

class BookRequest(BaseModel):
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    slot_time: Optional[str] = None

# In-Memory Database
PATIENTS = {
    "123456789": {
        "id": "123456789",
        "name": "ישראל ישראלי",
        "city": "תל אביב",
        "existing_appointments": [
            {"doctor": "ד״ר לוי (רופא משפחה)", "date": "02/09/2026", "time": "10:00", "clinic": "סניף מרכז - תל אביב"}
        ]
    },
    "987654321": {
        "id": "987654321",
        "name": "שרה כהן",
        "city": "חיפה",
        "existing_appointments": []
    },
    "112233445": {
        "id": "112233445",
        "name": "דוד מזרחי",
        "city": "ירושלים",
        "existing_appointments": [
            {"doctor": "ד״ר ישראלי (רופא עור)", "date": "04/09/2026", "time": "14:00", "clinic": "סניף צפון - חיפה"}
        ]
    },
    "556677889": {
        "id": "556677889",
        "name": "מיכל לוי",
        "city": "באר שבע",
        "existing_appointments": [
            {"doctor": "ד״ר אברהם (רופאת עיניים)", "date": "02/09/2026", "time": "08:30", "clinic": "סניף דרום - באר שבע"},
            {"doctor": "ד״ר לוי (רופא משפחה)", "date": "15/09/2026", "time": "11:30", "clinic": "סניף מרכז - תל אביב"}
        ]
    },
    "998877665": {
        "id": "998877665",
        "name": "אלון חסן",
        "city": "ראש העין",
        "existing_appointments": []
    }
}

DOCTORS = {
    "1": {"id": "1", "name": "ד״ר לוי", "specialty": "רופא משפחה", "clinic": "סניף מרכז - תל אביב"},
    "2": {"id": "2", "name": "ד״ר ישראלי", "specialty": "רופא עור", "clinic": "סניף צפון - חיפה"},
    "3": {"id": "3", "name": "ד״ר אברהם", "specialty": "רופאת עיניים", "clinic": "סניף דרום - באר שבע"}
}

AVAILABLE_SLOTS = {
    "1": ["01/09/2026 09:00", "01/09/2026 09:30", "02/09/2026 11:00"],
    "2": ["03/09/2026 12:00", "03/09/2026 12:30"],  
    "3": ["02/09/2026 09:00", "05/09/2026 10:30"] 
}

# ==========================================================
# פונקציית עזר להדפסת תמונת מצב של כל התורים במערכת
# ==========================================================
def log_appointments_state(stage_title: str):
    """
    מדפיסה בצורה קריאה ומובנת את כל התורים הפנויים והתורים המוזמנים במערכת.
    """
    separator = "=" * 70
    lines = [
        f"\n{separator}",
        f" 📋 תמונת מצב תורים במערכת: [{stage_title}]",
        separator,
        "🟢 תורים פנויים לקביעה (AVAILABLE SLOTS):"
    ]

    for doc_id, slots in AVAILABLE_SLOTS.items():
        doc = DOCTORS.get(doc_id, {"name": "לא ידוע", "specialty": ""})
        slots_str = ", ".join(slots) if slots else "אין תורים פנויים כרגע"
        lines.append(f"  • {doc['name']} ({doc['specialty']}): [{slots_str}]")

    lines.append("\n🔵 תורים מוזמנים אצל מטופלים (BOOKED APPOINTMENTS):")
    has_any_appointment = False
    for pid, pdata in PATIENTS.items():
        apts = pdata.get("existing_appointments", [])
        if apts:
            has_any_appointment = True
            lines.append(f"  • {pdata['name']} (ת.ז: {pid}):")
            for apt in apts:
                lines.append(f"      - {apt.get('doctor')} | תאריך ושעה: {apt.get('date')} {apt.get('time')} | מרפאה: {apt.get('clinic')}")
    
    if not has_any_appointment:
        lines.append("  (אין תורים מוזמנים לאף מטופל כרגע)")

    lines.append(f"{separator}\n")
    
    # הדפסה בלוג
    logger.info("\n".join(lines))


# 1. אימות מטופל
@app.post("/api/auth")
def authenticate_patient(req: Dict[str, Any]):
    logger.info(f"[START] התחלת אימות מטופל עם נתונים: {req}")
    id_num = str(req.get("id_number", "")).strip()
    patient = PATIENTS.get(id_num)
    if not patient:
        for pid, pdata in PATIENTS.items():
            if pid == id_num or pid in str(req):
                patient = pdata
                break
    if not patient:
        logger.warning(f"[FAIL] אימות נכשל: מטופל לא נמצא עבור {id_num}")
        raise HTTPException(status_code=404, detail="המטופל לא נמצא במערכת")
    
    logger.info(f"[SUCCESS] אימות הושלם בהצלחה עבור מטופל: {patient['name']} (ID: {patient['id']})")
    return {
        "status": "success",
        "patient_id": patient["id"],
        "name": patient["name"],
        "city": patient["city"],
        "existing_appointments": patient["existing_appointments"]
    }

# 2. מידע על מרפאות
@app.get("/api/clinics/info")
def get_clinics_info():
    logger.info("[START] התחלת שליפת מידע על מרפאות")
    data = {
        "clinics": [
            {"name": "מרכז - תל אביב", "address": "דיזנגוף 100", "services": ["רופא משפחה", "בדיקות דם", "רנטגן", "CT"]},
            {"name": "צפון - חיפה", "address": "שדרות הנשיא 45", "services": ["רופא עור", "פיזיותרפיה", "אולטרסאונד"]},
            {"name": "דרום - באר שבע", "address": "שדרות רגר 12", "services": ["רופאת עיניים", "אורתופדיה", "אק״ג"]}
        ]
    }
    logger.info(f"[SUCCESS] שליפת מידע על מרפאות הושלמה בהצלחה ({len(data['clinics'])} מרפאות)")
    return data

# 3. משיכת תורים פנויים
@app.post("/api/slots")
def get_slots(req: Dict[str, Any]):
    logger.info(f"[START] התחלת חיפוש תורים עם פרמטרים: {req}")
    doc_id = str(req.get("doctor_id", "")).strip()
    search_term = str(req.get("specialty", "") or req.get("doctor_name", "") or "").lower()
    
    if doc_id in AVAILABLE_SLOTS:
        doctor = DOCTORS[doc_id]
        logger.info(f"[SUCCESS] נמצאו תורים עבור רופא מזהה {doc_id} ({doctor['name']})")
        return {
            "doctor_id": doc_id,
            "doctor_name": doctor["name"],
            "specialty": doctor["specialty"],
            "clinic": doctor["clinic"],
            "available_slots": AVAILABLE_SLOTS[doc_id]
        }
    
    for did, doctor in DOCTORS.items():
        if (search_term and (search_term in doctor["specialty"] or search_term in doctor["name"])) or \
           did in str(req) or doctor["specialty"] in str(req) or doctor["name"] in str(req):
            logger.info(f"[SUCCESS] נמצאו תורים לפי חיפוש חופשי עבור {doctor['name']}")
            return {
                "doctor_id": did,
                "doctor_name": doctor["name"],
                "specialty": doctor["specialty"],
                "clinic": doctor["clinic"],
                "available_slots": AVAILABLE_SLOTS[did]
            }
            
    all_slots = []
    for did, slots in AVAILABLE_SLOTS.items():
        doc = DOCTORS[did]
        for s in slots:
            all_slots.append(f"{doc['name']} ({doc['specialty']} ב{doc['clinic']}): {s}")
            
    logger.info(f"[SUCCESS] הוחזרו כלל התורים הפנויים ({len(all_slots)} תורים זמינים)")
    return {"available_slots": all_slots}

# 4. קביעת תור
@app.post("/api/book")
def book_slot(req: Dict[str, Any]):
    logger.info(f"[START] התחלת קביעת תור: {req}")
    
    # הדפסת מצב התורים לפני השינוי
    log_appointments_state("לפני קביעת תור")

    p_id = str(req.get("patient_id", "")).strip()
    d_id = str(req.get("doctor_id", "1")).strip()
    slot_time = str(req.get("slot_time", "")).strip()
    
    if d_id not in AVAILABLE_SLOTS:
        for did, slots in AVAILABLE_SLOTS.items():
            if slot_time in slots:
                d_id = did
                break
        else:
            d_id = "1"

    doctor = DOCTORS.get(d_id, DOCTORS["1"])
    
    # עדכון נתונים 1: הסרת התור מרשימת הפנויים
    if d_id in AVAILABLE_SLOTS and slot_time in AVAILABLE_SLOTS[d_id]:
        AVAILABLE_SLOTS[d_id].remove(slot_time)
        logger.info(f"[DATA MUTATION] התור '{slot_time}' הוסר מהתורים הפנויים של {doctor['name']}")
        
    # עדכון נתונים 2: הוספת התור לרשומת המטופל
    if p_id in PATIENTS:
        new_appointment = {
            "doctor": f"{doctor['name']} ({doctor['specialty']})",
            "date": slot_time.split()[0] if slot_time else "בקרוב",
            "time": slot_time.split()[1] if len(slot_time.split()) > 1 else "",
            "clinic": doctor["clinic"]
        }
        PATIENTS[p_id]["existing_appointments"].append(new_appointment)
        logger.info(f"[DATA MUTATION] תור חדש התווסף למטופל {PATIENTS[p_id]['name']}: {new_appointment}")

    # הדפסת מצב התורים אחרי השינוי
    log_appointments_state("אחרי קביעת תור")

    logger.info(f"[SUCCESS] קביעת התור הושלמה בהצלחה עבור מטופל {p_id}")
    return {
        "status": "confirmed",
        "message": f"התור נקבע בהצלחה ל-{doctor['name']} ({doctor['specialty']}) במועד {slot_time}",
        "details": {
            "patient_id": p_id,
            "doctor": doctor["name"],
            "time": slot_time,
            "clinic": doctor["clinic"]
        }
    }

# 5. ביטול תור
@app.post("/api/cancel")
def cancel_appointment(req: Dict[str, Any]):
    logger.info(f"[START] התחלת ביטול תור: {req}")
    p_id = str(req.get("patient_id", "")).strip()
    slot_time = str(req.get("slot_time", "")).strip()
    doctor_name = str(req.get("doctor_name", "")).strip()
    
    patient = PATIENTS.get(p_id)
    if not patient:
        for pid, pdata in PATIENTS.items():
            if pid == p_id or pid in str(req):
                patient = pdata
                p_id = pid
                break

    if not patient:
        logger.warning(f"[FAIL] ביטול תור נכשל: מטופל {p_id} לא נמצא")
        raise HTTPException(status_code=404, detail="מטופל לא נמצא")

    # הדפסת מצב התורים לפני הביטול
    log_appointments_state("לפני ביטול תור")

    removed_apt = None
    remaining_apts = []
    for apt in patient["existing_appointments"]:
        if (slot_time and (slot_time in apt.get("time", "") or slot_time in apt.get("date", "") or slot_time in str(apt))) or \
           (doctor_name and doctor_name in apt.get("doctor", "")):
            removed_apt = apt
        else:
            remaining_apts.append(apt)
            
    if not removed_apt and len(patient["existing_appointments"]) > 0:
        removed_apt = patient["existing_appointments"].pop()
    else:
        patient["existing_appointments"] = remaining_apts

    if not removed_apt:
        logger.warning(f"[FAIL] ביטול נכשל: לא נמצא תור תואם עבור מטופל {p_id}")
        return {"status": "error", "message": "לא נמצא תור תואם לביטול"}

    # עדכון נתונים 1: הסרת התור מהמטופל
    logger.info(f"[DATA MUTATION] תור הוסר מרשומת המטופל {patient['name']}: {removed_apt}")

    # עדכון נתונים 2: החזרת התור לרשימת הפנויים
    for did, doc in DOCTORS.items():
        if doc["name"] in removed_apt.get("doctor", ""):
            reconstructed_slot = f"{removed_apt.get('date')} {removed_apt.get('time')}".strip()
            if reconstructed_slot and reconstructed_slot not in AVAILABLE_SLOTS[did]:
                AVAILABLE_SLOTS[did].append(reconstructed_slot)
                AVAILABLE_SLOTS[did].sort()
                logger.info(f"[DATA MUTATION] התור '{reconstructed_slot}' הוחזר לתורים הפנויים של {doc['name']}")

    # הדפסת מצב התורים אחרי הביטול
    log_appointments_state("אחרי ביטול תור")

    logger.info(f"[SUCCESS] ביטול התור הושלם בהצלחה עבור מטופל {p_id}")
    return {
        "status": "cancelled",
        "message": f"התור עבור {removed_apt.get('doctor')} בתאריך {removed_apt.get('date')} בוטל בהצלחה."
    }

@app.get("/health-check")
def health_check():
    logger.info("[START] בדיקת תקינות מערכת (Health Check)")
    logger.info("[SUCCESS] בדיקת תקינות הושלמה בהצלחה")
    return {"status": "ok"}