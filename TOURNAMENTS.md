# Private tournaments

Use **Tournaments → Create tournament**, choose a name, capacity (4–16) and clock (3, 5, 10, 15 or 30 minutes per player), then share the invitation link. A signed-in account is required. The organizer joins automatically and can start with at least two players; the capacity is a maximum, not a requirement.

The link grants access to the lobby and registration. Only participants can read match schedules or the live state. Only the organizer can start or cancel a lobby. Registration and leaving close at start. Each round has one match per player; the next opens after all results are confirmed. Standings update automatically. Equal scores share a place, and every player receives one one-point bye when the participant count is odd. Games are casual and do not affect Elo.

Scores: win 1, draw ½, loss 0. White/black assignments differ by at most one game per player. Future-round clocks do not run before their games are created; newly opened clocks begin on the first move under existing game rules. Players should agree to be available before the host starts: this version has no scheduled starts or automatic forfeits for absent players.

Migration: `python manage.py migrate` applies `0022_tournament_tournamententry_tournamentmatch_and_more`. The existing Docker build already runs migrations. No production deployment has been triggered by this change.

Verification: `python manage.py test games.test_tournaments --settings=config.test_settings`.

Hosts can invite accepted friends from the lobby. Invitations appear under Notifications; opening the tournament does not enroll a player. Players explicitly join, subject to capacity and registration status. Each new round creates one private notification per participant (including byes); opening the tournament clears that round notice. Old invitations disappear after registration closes. Migration 0023 stores notices. Mobile standings show rank, player and points; full win/draw/loss columns remain available on desktop.
