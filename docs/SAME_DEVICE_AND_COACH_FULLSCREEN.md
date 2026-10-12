# Shared-device chess and fullscreen coach replies

Same-device play: /play/same-device/, available under Games. Public, two people take alternating turns using the existing movement/rule engine. No bot, matchmaking, server game writes, Elo, XP, or account requirement. Separate sessionStorage state restores the game in this tab. Includes review navigation, automatic board flip option, fullscreen, confirmation before replacing an unfinished game, result summary and optional existing PGN analysis. First version has no clock. It does not join the online/coach active-game selector.

A LOCAL_PLAY_MODE guard prevents move and finish requests in both source and shipped board artifacts. It does not change multiplayer or coach behavior. No migrations are needed.

Fullscreen coach fix: coach_access moves the response bubble into the chat dock while that dock belongs to the fullscreen subtree. Existing replies, new asynchronous replies and automatic advice all use that placement. Responses return to their regular desktop or mobile location after exit. Closing a reply and repeated fullscreen transitions preserve the chat history. This solves the native-browser restriction where a body-level response is invisible outside the fullscreen element, and avoids overlaying the board.

Verification: client regression for coach replies in both viewport classes; real local question/response flow in fullscreen; shared-device guest page in PT/ES/EN; both human turns and Fool's Mate on the actual board; refresh restores the finished game; source/shipped guards tested without network; existing chess/client suites. Preview server and fixture database are separate from production. No commit or deploy performed.
