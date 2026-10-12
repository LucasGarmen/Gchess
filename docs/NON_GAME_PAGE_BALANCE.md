# Compact non-game screens

page_balance.css is scoped to page-specific containers. No game layouts, squares, pieces, coach replies, or fullscreen are targeted. Gameplay, authentication, rewards, friendship and tournament logic are unchanged.

Create-game options are bounded to 920px, with smaller spacing and a desktop time input beside its label. Training places its recommended session beside the existing XP summary, followed by exercises/openings. Reading order follows that hierarchy. Friends places search next to contacts; ranking and weekly features are native details, with ranking reopened when choosing a metric. Empty contacts show a short actionable state. Actual search, requests, statistics and challenge forms remain available; populated lists wrap cards naturally. Analysis import, opening catalog, blindfold landing and tournament creation receive bounded widths and spacing. Active game/training boards are not restyled.

Mobile layouts stack and preserve scrolling for long lists and validation errors. No fixed page heights, hidden overflow, filler statistics or dependencies. No migration required. Preview uses a separate local database; commit and deploy remain with the user.
