# Phase 4: optimization, accessibility and first-party metrics

## Runtime changes

Notification polling skips hidden tabs, rejects overlapping fetches, refreshes when visible, and stops on expired authentication. Game result DOM notifications are batched into one animation frame. PlayerActivityDay lookups are cached for five minutes after successful persistence; the cache includes account creation time to avoid collisions across recreated accounts. JSON polling no longer increments DailyVisit page-view totals. Presence updates keep their existing cooldown and semantics.

No new client dependencies, analytics vendors, engine analysis, or Gemini calls were added. XP rewards do not run again for unrelated game field saves. Core movement and analysis code remain unchanged.

## Keyboard and mobile

The board is one Tab stop with arrow navigation in visual order, including flipped boards. Enter/space use existing square click behavior; accessible labels follow final piece mutations after animation. Selection uses aria-pressed. Changes to labels are coalesced; keyboard support does not delay moves. Result summaries close with Escape. Fullscreen focus cycling includes selects and the board. Focus outlines remain visible on textured boards.

Fullscreen on short landscape screens uses a side-by-side board/chat layout, rather than reserving portrait-height chat space. Result panels adapt to short viewport height and scroll internally when necessary. Reduced animation settings preserve all information and suppress decorative transitions. Current browser checks cover desktop, 390x844 portrait, and 844x390 landscape; these do not substitute for testing physical mobile devices or all assistive technologies.

## Private retention panel

Admin > Actividad de jugadores includes 30-day counts of registered players who start (first saved move), finish, start another game after finishing, and save post-game analysis. First-party GameExperienceEvent contains only user/game references, event kind, date and timestamp. No IPs, browser fingerprints, chat content or third-party transmissions. Events are recorded after transaction commit, deduplicated per user/game/kind, and indexed for summary queries.

Existing activity/returning-day counts and CSV export are preserved. Counts are unique users per event, not a conversion cohort or percentages. Started/finished game counts are separately displayed. Staff, inactive accounts and guests are excluded. Browser-only coach games are not persisted and are explicitly outside this initial metric scope. History begins when tracking is deployed; reopening old finished games never fabricates starts/finishes. Records cascade with deleted users/games.

Migration: games/0040_gameexperienceevent.py. Run manage.py migrate before serving this version. The existing Docker startup migration step applies it on deploy. No production migration or deployment was performed by the agent.

Performance work reduces unnecessary requests and queries, but no claim is made about resolving the user's earlier unspecified slowdown. Profiling that specific behavior and a production load test remain follow-up work.
