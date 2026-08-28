# HealthVoice AI - Voice Agent & Clinic Backend System

An autonomous, voice-first medical clinic assistant integrating **AudioCodes LiveHub**, a **FastAPI** REST backend deployed on **Render**, and a **Knowledge Base (RAG)** document system.

---

## 🌟 Overview & Architecture

The system enables patients to interact with a clinic voice agent in natural Hebrew to:
* Verify identity via Israeli ID and retrieve patient records and residency.
* Inquire about clinic branches, operating hours, and specialized services using Knowledge Base Documents.
* View upcoming appointments.
* Book new appointments from real-time available slots.
* Cancel or reschedule existing appointments with explicit user confirmation.

                ┌─────────────────────────┐
                │     User / Caller       │
                └───────────┬─────────────┘
                            │ (Voice Dialogue)
                ┌───────────▼─────────────┐
                │   AudioCodes LiveHub    │
                │   (HEALTHVOICE-AGENT)   │
                └───────┬─────────┬───────┘
                        │         │
           Knowledge/RAG│         │ REST Tools (JSON)
                        ▼         ▼
    ┌─────────────────────┐     ┌────────────────────────────┐
    │  clinics_info.txt   │     │  FastAPI Backend (Render)  │
    │ (Branches, Services)│     │  https://healthvoice-api...│
    └─────────────────────┘     └────────────────────────────┘


  ---

## 🛠️ API Endpoints

Base URL: `https://healthvoice-api.onrender.com`

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/auth` | `POST` | Authenticate patient by ID, return city and existing appointments |
| `/api/clinics/info` | `GET` | General clinic metadata and services fallback |
| `/api/slots` | `POST` | Fetch open slots by doctor ID, doctor name, or specialty |
| `/api/book` | `POST` | Book a new slot and update patient record |
| `/api/cancel` | `POST` | Cancel an existing appointment and restore slot availability |

---

## 🧪 Test Personas & Scenarios

### Test IDs in Database
* **`123456789`** – ישראל ישראלי (תל אביב) | Has upcoming appointment with ד״ר לוי.
* **`556677889`** – מיכל לוי (באר שבע) | Has upcoming appointments with ד״ר אברהם and ד״ר לוי.
* **`987654321`** – שרה כהן (חיפה) | No existing appointments (ideal for booking flows).

### Recommended Test Scenarios
1. **Clinic Knowledge (RAG):** Ask about specific medical services without logging in (e.g., *"איפה עושים בדיקות דם?"* or *"מה שעות הפעילות בחיפה?"*).
2. **Patient Lookup & Existing Slots:** Identify using ID `123456789` and ask *"מתי התור הבא שלי?"*.
3. **Appointment Cancellation:** Ask to cancel the appointment with Dr. Levi, verify confirmation prompt, and confirm.
4. **Appointment Booking:** Request to book an appointment with a dermatologist (רופא עור), choose an available slot, and receive confirmation.

---
