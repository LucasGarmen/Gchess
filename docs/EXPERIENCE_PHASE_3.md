# Phase 3: earned XP and activity progress

XP reuses UserPuzzleStats totals and levels (100 XP per level). Historic totals stay intact. Existing XP/level achievements remain supported. Elo, puzzle rating, and the 10-point daily check-in are independent.

Rewards are verified server-side and recorded once in LearningReward. Records and totals are updated atomically with a lock on the user's statistics row. A unique user/key constraint prevents duplicate claims. The progress GET endpoint is read-only, authenticated, and checks game ownership.

| Activity | Reward | Limits |
| --- | --- | --- |
| First correct solution to an exercise | Existing difficulty-based XP | 100 XP/day; same puzzle never repeats |
| Completed daily session | 20 XP | At least one answer solved rather than revealed; once per session date |
| Completed weekly challenge | 25 XP | At least one first-attempt correct answer; practice replays earn nothing |
| Saved engine review | 10 XP | At least 4 half-moves; two/day; same starting position and move sequence never repeats across languages or PGN headers |
| Finished human game | 5 XP regardless of result | Both players registered, at least 12 half-moves, three/day and one per opponent/day |

Daily caps and activity streaks use America/Fortaleza dates. Zero-XP capped first completions are recorded too, so replaying them tomorrow cannot bypass a cap. A streak counts consecutive days with positive earned XP through today or yesterday; check-in alone does not count. Temporary browser-only coach games do not earn completion XP. Their saved engine reviews can qualify.

The compact dashboard appears in Training and My learning. Daily and weekly completion summaries show persisted XP. The human game result fetches actual reward XP without delaying result or rematch controls. No fictitious accuracy, rewards, or streaks are shown.

Migration: games/0039_learningreward.py. Run manage.py migrate before serving this code; Render's existing migration step should apply it on deploy. No backfill: historical exercise attempts cannot be reliably reconstructed from the existing last-puzzle field, so first-solve deduplication starts with this release. Existing XP is never reset.

Caps and reward values are defined in games/rewards.py and the established puzzle difficulty helper in games/views.py. The admin ledger is read-only. Production concurrency uses database row locking; the local SQLite suite verifies idempotency and the uniqueness constraint but is not a substitute for PostgreSQL load testing.
