# Experience phases 1 and 2

The existing rustic UI, board, engine, trainer, authentication and storage are retained.

- Last-move and check marks remain visible on material board themes. Piece movement remains brief; capture feedback adds no awaited delay.
- The motion control persists locally and respects system reduced-motion preferences. Home animation, menus and result feedback respect it.
- The existing sound and volume controls remain. Repeated playback no longer attenuates volume cumulatively; mute/volume sync between tabs. Quiet capture/check/result cues use the shared Web Audio context without new dependencies. Decisive moves defer their sound to the result; repeated/replayed results are deduplicated.
- The board result card handles victory, defeat and draw from the player perspective, shows actual ply/capture counts, and reuses coach replay, human rematch and PGN analysis. It can be dismissed and reopened. It travels into fullscreen and keeps its buttons usable. Empty games do not offer a meaningless analysis.
- Resignation, agreed draw and timeout notify connected participants through a separate `game.state` event after transaction commit, without treating it as a move acknowledgement.
- No new XP economy, accuracy estimate, reward model or retention tracking was added. Puzzle XP remains separate from game results. No database migration is required.

Tests: client scripts cover preferences/audio, reduced motion, fullscreen, result perspective, real counts, action routing, dismissal and sound deduplication. Django checks cover commit timing, participant access, native rematch form, translations and existing game/trainer/auth flows. Browser checks used a separate local preview database for capture persistence, live opponent resignation, fullscreen rematch, mobile layout and one-click coach replay.
