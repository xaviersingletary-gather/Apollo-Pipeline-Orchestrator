# Reply Classifier — Pattern List

This file is the source of truth for the watcher's reply classifier. The watcher reads this file every run and applies the patterns below. Update it as Peter labels misses.

Version: v1 (2026-05-29). Will drift as we tune.

---

## OOO patterns

Trigger when the reply body matches ANY of these signals AND the message is short / has auto-reply formatting (single paragraph, third-person tone, no real question to the sender).

- "out of office" / "OOO" / "out of the office"
- "on vacation" / "on holiday" / "on PTO" / "on leave"
- "on parental leave" / "on maternity leave" / "on paternity leave"
- "on sabbatical"
- "will be back on [date]" / "returning [date]" / "back in office on..."
- "limited access to email" / "checking email intermittently"
- "for urgent matters please contact [X]"
- Common auto-reply scaffolding: "Thank you for your email" + "I am currently away"

## Wrong-person patterns

Trigger when the reply indicates the message reached the wrong recipient or an inappropriate one.

- "no longer with the company" / "no longer here" / "has left"
- "you have the wrong person" / "I'm not the right person" / "not my area"
- "I don't handle that" / "I don't manage that"
- "please contact [X] instead" / "redirecting you to..." / "loop in [X]"
- "remove me from your list" / "unsubscribe" / "do not email me again" / "stop emailing"
- "this is not [name]" / "you've reached me in error" / "this email is no longer monitored"
- "I retired"

## Real-response default

Anything that does not match the patterns above is classified as **real**. This includes:

- "tell me more" / "send me more info"
- "not interested" / "we're not a fit" / "we use [competitor]"
- "I'll think about it" / "let me discuss internally"
- "what's the price?" / "what does this cost?"
- "schedule a call" / "book a meeting"
- Any substantive engagement with the pitch

Bias toward classifying as real when uncertain. False positives are easier to filter than false negatives.

---

## Tuning log

Append entries here when Peter labels a misclassification. Format:

```
YYYY-MM-DD — [classification we made] should have been [correct classification]
Reply excerpt: "..."
Pattern added/removed: ...
```

(Empty — this is v1.)
