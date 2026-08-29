# HealthVoice AI - Voice Agent & Clinic Management Backend

A voice-first medical clinic assistant integrating **AudioCodes LiveHub**, a **FastAPI** REST backend deployed on **Render**, and a **Knowledge Base (RAG)** document system.

---

## 🌟 Overview

The system enables patients to interact with a clinic voice agent in natural Hebrew to:
* Verify identity via Israeli ID, retrieve residency, and view active appointments from the database.
* Inquire about clinic branches, operating hours, and specialized medical services using Knowledge Base documents (RAG).
* Fetch open doctor appointments in real time.
* Book new appointments with immediate data mutation across slots and patient records.
* Cancel existing appointments with explicit user confirmation and slot release.


---

## 🛠️ API Endpoints

Base URL: `https://healthvoice-api.onrender.com`

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/health-check` | `GET` | Health check endpoint confirming API availability |
| `/api/auth` | `POST` | Authenticate patient by ID, return city and existing appointments |
| `/api/slots` | `POST` | Fetch open appointment slots by clinic or specialty |
| `/api/book` | `POST` | Book a new slot, remove it from availability, and add to patient records |
| `/api/cancel` | `POST` | Cancel an appointment and return the slot back to availability |

---

## 🧪 Test Personas & Scenarios

### Test IDs in Database
* **`123456789`** – ישראל ישראלי (תל אביב) | Has an active appointment with ד״ר לוי (רופא משפחה).
* **`556677889`** – מיכל לוי (באר שבע) | Has active appointments with ד״ר אברהם (רופאת עיניים) and ד״ר לוי.
* **`112233445`** – דוד מזרחי (ירושלים) | Has an active appointment with ד״ר ישראלי (רופא עור).
* **`987654321`** – שרה כהן (חיפה) | No active appointments (ideal for booking flows).
* **`998877665`** – אלון חסן (ראש העין) | No active appointments.

### Recommended Test Scenarios
1. **Patient Lookup & Existing Appointments:** Identify with ID `123456789` and ask *"מתי התור הקרוב שלי?"*.
2. **Appointment Cancellation:** Ask to cancel the appointment with Dr. Levi, verify confirmation prompt, and complete cancellation.
3. **Appointment Booking:** Request to book an appointment with a dermatologist (רופא עור) or family doctor, choose an available slot, and receive confirmation.

---