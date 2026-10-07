# Tournaments

Use **Tournaments → Create tournament**, choose public or private visibility, a name, capacity (4–16) and clock (3, 5, 10, 15 or 30 minutes per player), then share the invitation link. A signed-in account is required. The organizer joins automatically and can start with at least two players; the capacity is a maximum, not a requirement.

Public tournaments are discoverable by signed-in users. Private tournaments require the shared password to register; nonmembers cannot read their roster or schedules. Only participants can read the live state. Only the organizer can start or cancel a lobby. Registration and leaving close at start. Each round has one match per player; the next opens after all results are confirmed. Standings update automatically. Equal scores share a place, and every player receives one one-point bye when the participant count is odd. Games are casual and do not affect Elo.

Scores: win 1, draw ½, loss 0. White/black assignments differ by at most one game per player. Future-round clocks do not run before their games are created; newly opened clocks begin on the first move under existing game rules. Players should agree to be available before the host starts: this version has no scheduled starts or automatic forfeits for absent players.

Migration: `python manage.py migrate` applies `0022_tournament_tournamententry_tournamentmatch_and_more`. The existing Docker build already runs migrations. No production deployment has been triggered by this change.

Verification: `python manage.py test games.test_tournaments --settings=config.test_settings`.

Hosts can invite accepted friends from the lobby. Invitations appear under Notifications; opening the tournament does not enroll a player. Players explicitly join, subject to capacity and registration status. Each new round creates one private notification per participant (including byes); opening the tournament clears that round notice. Old invitations disappear after registration closes. Migration 0023 stores notices. Mobile standings show rank, player and points; full win/draw/loss columns remain available on desktop.

## Public and password-protected tournaments
Migration 0025 adds visibility (existing tournaments remain private) and a password hash. New private tournaments require a 6–128 character shared password. Django hashes it; raw passwords are never stored, redisplayed, put in links or included in invitations. Friends and link visitors enter the password when joining. Existing members retain access. Leaving and rejoining requires the current password again. Only the host may set or rotate it, while registration is open. Older lobbies require password setup before new enrollment or starting; active and completed tournaments continue normally for enrolled users.

Public tournaments appear in a paginated directory filtered by open registration, active or finished. All signed-in users may see their standings; game access remains participant-only. Private nonmembers see only the title, status, capacity and time, plus the join form. Hosts still start manually and capacity checks use the tournament transaction lock. Password attempts are limited to eight per minute per signed-in account; join and password changes require CSRF-protected POST. Visibility is selected at creation and cannot be changed afterward.
