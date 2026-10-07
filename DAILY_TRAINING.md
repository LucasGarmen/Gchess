# Daily training

Training > Today’s training contains three single-move positions. Signed-in users start with a CSRF-protected POST. One frozen plan per account per UTC calendar date is saved, including attempts, hints, viewed solutions and completion. Opening the page never creates a record. Sessions can be resumed across devices.

Personal positions come only from that account’s saved GameReview errors with a legal, engine-verified recommendation and a known positive loss. Positions are deduplicated across languages and rotated among recent serious mistakes; previously unseen positions are preferred where at least three are available. Missing or invalid analysis is excluded. Remaining slots use existing mate-in-one positions, verified for legal checkmate with python-chess. No Gemini or fresh engine request is made during training. This version does not infer tactical weaknesses or auto-analyze finished games: users need to save a game analysis first.

The backend validates legal moves against the frozen FEN and keeps solutions private until solved or revealed. Alternative checkmates are accepted. Other legal alternatives receive a neutral response: saved analysis does not prove that every other move is bad. Explanations use verified board facts, never invented engine variations. Completion reports first-try unassisted solutions separately from positions completed with hints, revealed solutions or retries. No Elo, puzzle rating or XP changes are awarded.

Migration 0024 adds DailyTraining. Test with DATABASE_URL empty and config.test_settings: manage.py test games.test_daily_training games.test_training games.test_learning --settings=config.test_settings.
