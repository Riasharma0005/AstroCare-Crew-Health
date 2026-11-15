# AstroCare: Crew Health Intelligence

A connected health companion for astronauts on long missions, built for the NASA Space Apps Challenge
"Create Health Monitoring Software for Astronauts on Space Missions".

## Run it
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
First launch creates a 30-day Mars demo mission (simulated data) with three crew members.

## Seven views
| View | What it does |
|---|---|
| Mission Control | Status, mission trajectory, daily missions, connected insights, story and poem cards |
| Health Lab | Daily check-in, trends with personal baselines, status map, how-to guides, flight-surgeon report |
| Body Explorer | Clickable body, NASA hazard highlighter, NASA risk atlas |
| Hazard Zone | NASA's five hazards, daily hazard log, delay simulator, hazard interplay |
| Creative Corner | Story chronicle, daily log, private diary, and a Reading corner (Ria Sharma's poems + crew shelf) |
| Pip Companion | Friendly rule-based alien guide that answers from your own data |
| Game Zone | Asteroid Dodge, Reflex Test, Planet Memory, Orbit Breathing, Hazard Quiz |

Professional mission-control styling everywhere; the cute planets and aliens live in Pip and the Game Zone.

## Sources
NASA Human Research Program: Hazards, Risks, Ongoing research. Canadian Space Agency: radiation monitoring and science in space.
AstroCare paraphrases these for education and is not an official NASA or CSA product.

## Notes
Rule-based and transparent. Educational prototype, not a diagnostic tool. All demo data is simulated; the two other crew members and their poems are samples.
Original poems by Ria Sharma.
