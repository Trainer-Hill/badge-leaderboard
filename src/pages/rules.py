import dash
import dash_bootstrap_components as dbc
from dash import html, dcc


dash.register_page(__name__, path='/rules')


RULES = '''
# 🏅 Badge Earning System

*This system offers an opportunity to communities to reward players for their competitive performance throughout the season. The following rules will be implemented for awarding badges during the 2026 Pokemon Championship Series Season. These rules serve as the current structure and may be revised in the future.*

---

## 🛠️ How to Earn a Badge

Currently, Trainers in our community can earn a Badge in one of two ways:

1. **Win a Qualifying Event**  
   * **Win all rounds** (x-0) or **place first overall** (only events with 4 or more rounds)  
2. **Advance to Phase Two of a Major Event**  
   * Must be an officially recognized major event (e.g., Regionals, Specials, Internationals)

---

## ✅ Qualifying Event Requirements

A Qualifying Event must meet both of the following requirements to count towards Badge eligibility:

* Be posted in the community events list  
* Meet format-specific minimums:  
  * **Alternative formats (GLC / Expanded / Retro):** at least **8 players**  
  * **Standard:** at least **4 total rounds**

---

## 📊 Leaderboard Rankings

Leaderboards will track player performance in two categories:

* **Overall Season**  
* **Current Quarter** 

Rankings are based on the total number of badges earned. Tiebreakers will be determined by the sum of points earned (see below).

---

## 🎯 Points Breakdown (for Tiebreakers)

Points are awarded based on the level of the event where the badge was earned:

* **Locals / Online** - 1 point  
* **League Challenge** - 2 points  
* **League Cup** - 3 points  
* **Regionals / Specials / Internationals Championship** - 5 points

---

## 📓 Changelog

**2026 Season Start**

* Advancing to Phase 2 of a Major event earns a badge  
* Non Standard format badge requirement change from minimum 4 rounds to minimum 8 players  
* Tiebreakers are no longer based on unique decks  
* Tiebreakers are based on points earned

'''


def layout():
    """Render the rules page."""
    return dbc.Container([
        dcc.Markdown(
            RULES,
            id='rules-markdown'
        )
    ], fluid=True)
