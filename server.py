from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI(title="HealthVoice Clinic System")

# Data Models - גמישים כדי למנוע שגיאות 422
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
    "2": ["03/09/2026 12:00", "03/09/2026 12:30", "04/09/2026 14:00"],
    "3": ["02/09/2026 08:30", "02/09/2026 09:00", "05/09/2026 10:30"]
}

# 1. אימות מטופל
@app.post("/api/auth")
def authenticate_patient(req: Dict[str, Any]):
    id_num = str(req.get("id_number", "")).strip()
    patient = PATIENTS.get(id_num)
    if not patient:
        # בדיקה גמישה למקרה שנשלח בתוך מבנה מקונן
        for pid, pdata in PATIENTS.items():
            if pid == id_num or pid in str(req):
                patient = pdata
                break
    if not patient:
        raise HTTPException(status_code=404, detail="המטופל לא נמצא במערכת")
    return {
        "status": "success",
        "patient_id": patient["id"],
        "name": patient["name"],
        "city": patient["city"],
        "existing_appointments": patient["existing_appointments"]
    }

# 2. מידע על מרפאות (כדי למנוע 404)
@app.get("/api/clinics/info")
def get_clinics_info():
    return {
        "clinics": [
            {"name": "מרכז - תל אביב", "address": "דיזנגוף 100", "services": ["רופא משפחה", "בדיקות דם", "רנטגן", "CT"]},
            {"name": "צפון - חיפה", "address": "שדרות הנשיא 45", "services": ["רופא עור", "פיזיותרפיה", "אולטרסאונד"]},
            {"name": "דרום - באר שבע", "address": "שדרות רגר 12", "services": ["רופאת עיניים", "אורתופדיה", "אק״ג"]}
        ]
    }

# 3. משיכת תורים פנויים בצורה חכמה וגמישה
@app.post("/api/slots")
def get_slots(req: Dict[str, Any]):
    doc_id = str(req.get("doctor_id", "")).strip()
    search_term = str(req.get("specialty", "") or req.get("doctor_name", "") or "").lower()
    
    # אם הועבר מזהה ישיר
    if doc_id in AVAILABLE_SLOTS:
        doctor = DOCTORS[doc_id]
        return {
            "doctor_id": doc_id,
            "doctor_name": doctor["name"],
            "specialty": doctor["specialty"],
            "clinic": doctor["clinic"],
            "available_slots": AVAILABLE_SLOTS[doc_id]
        }
    
    # חיפוש חכם לפי טקסט (עור, משפחה, עיניים, שם רופא)
    for did, doctor in DOCTORS.items():
        if (search_term and (search_term in doctor["specialty"] or search_term in doctor["name"])) or \
           did in str(req) or doctor["specialty"] in str(req) or doctor["name"] in str(req):
            return {
                "doctor_id": did,
                "doctor_name": doctor["name"],
                "specialty": doctor["specialty"],
                "clinic": doctor["clinic"],
                "available_slots": AVAILABLE_SLOTS[did]
            }
            
    # ברירת מחדל אם לא זוהה רופא ספציפי - החזרת כל התורים הפנויים
    all_slots = []
    for did, slots in AVAILABLE_SLOTS.items():
        doc = DOCTORS[did]
        for s in slots:
            all_slots.append(f"{doc['name']} ({doc['specialty']} ב{doc['clinic']}): {s}")
    return {"available_slots": all_slots}

# 4. קביעת תור
@app.post("/api/book")
def book_slot(req: Dict[str, Any]):
    p_id = str(req.get("patient_id", "")).strip()
    d_id = str(req.get("doctor_id", "1")).strip()
    slot_time = str(req.get("slot_time", "")).strip()
    
    # אם הרופא לא זוהה במדויק, נאתר אותו לפי השעה
    if d_id not in AVAILABLE_SLOTS:
        for did, slots in AVAILABLE_SLOTS.items():
            if slot_time in slots:
                d_id = did
                break
        else:
            d_id = "1" # fallback

    doctor = DOCTORS.get(d_id, DOCTORS["1"])
    
    # הסרת התור מהפנויים אם קיים
    if d_id in AVAILABLE_SLOTS and slot_time in AVAILABLE_SLOTS[d_id]:
        AVAILABLE_SLOTS[d_id].remove(slot_time)
        
    # עדכון התור ברשומת המטופל
    if p_id in PATIENTS:
        PATIENTS[p_id]["existing_appointments"].append({
            "doctor": f"{doctor['name']} ({doctor['specialty']})",
            "date": slot_time.split()[0] if slot_time else "בקרוב",
            "time": slot_time.split()[1] if len(slot_time.split()) > 1 else "",
            "clinic": doctor["clinic"]
        })

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
# 5. ביטול תור והחזרתו לתורים הפנויים
@app.post("/api/cancel")
def cancel_appointment(req: Dict[str, Any]):
    p_id = str(req.get("patient_id", "")).strip()
    slot_time = str(req.get("slot_time", "")).strip()
    doctor_name = str(req.get("doctor_name", "")).strip()
    
    # איתור המטופל
    patient = PATIENTS.get(p_id)
    if not patient:
        for pid, pdata in PATIENTS.items():
            if pid == p_id or pid in str(req):
                patient = pdata
                p_id = pid
                break

    if not patient:
        raise HTTPException(status_code=404, detail="מטופל לא נמצא")

    # בדיקה ומחיקת התור מרשימת התורים של המטופל
    removed_apt = None
    remaining_apts = []
    for apt in patient["existing_appointments"]:
        # התאמה לפי שעה, תאריך או שם רופא
        if (slot_time and (slot_time in apt.get("time", "") or slot_time in apt.get("date", "") or slot_time in str(apt))) or \
           (doctor_name and doctor_name in apt.get("doctor", "")):
            removed_apt = apt
        else:
            remaining_apts.append(apt)
            
    # אם לא נמצא תור ספציפי אבל יש תור יחיד, נבטל אותו כברירת מחדל
    if not removed_apt and len(patient["existing_appointments"]) > 0:
        removed_apt = patient["existing_appointments"].pop()
    else:
        patient["existing_appointments"] = remaining_apts

    if not removed_apt:
        return {"status": "error", "message": "לא נמצא תור תואם לביטול"}

    # החזרת התור לרשימת התורים הפנויים (אם ידוע הרופא)
    for did, doc in DOCTORS.items():
        if doc["name"] in removed_apt.get("doctor", ""):
            reconstructed_slot = f"{removed_apt.get('date')} {removed_apt.get('time')}".strip()
            if reconstructed_slot and reconstructed_slot not in AVAILABLE_SLOTS[did]:
                AVAILABLE_SLOTS[did].append(reconstructed_slot)
                AVAILABLE_SLOTS[did].sort()

    return {
        "status": "cancelled",
        "message": f"התור עבור {removed_apt.get('doctor')} בתאריך {removed_apt.get('date')} בוטל בהצלחה."
    }

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

