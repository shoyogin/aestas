"""Shared cycle copy. Friend = lite (no drive). Partner = full panels + support line."""

PHASE_LABELS = {
    "menstrual": "Menstrual",
    "follicular": "Follicular",
    "ovulation": "Ovulation",
    "luteal": "Luteal",
}

PARTNER_SUPPORT = {
    "menstrual": "Offer rest, heat, and low-key plans — skip pressure to go out or perform.",
    "follicular": "Energy is rising: good time for dates, new plans, and light adventure.",
    "ovulation": "They may feel extra social or sensual; check in, and respect the fertile window.",
    "luteal": "Patience and smaller plans help; don’t take irritability personally.",
}

FRIEND_LITE = {
    "menstrual": {
        "food": {
            "title": "Nourish",
            "bullets": ["Warm, iron-rich meals help.", "Hydration and rest beat restriction."],
            "why": "This phase often asks for gentleness.",
        },
        "activity": {
            "title": "Gentle movement",
            "bullets": ["Walks and stretching over max effort.", "Sleep counts as recovery."],
            "why": "Energy is often lower at the start of the cycle.",
        },
        "mood": {
            "title": "Soft awareness",
            "bullets": ["Shorter plans are enough.", "This dip is cyclic, not a character flaw."],
            "why": "Mood can flatten when hormones drop.",
        },
    },
    "follicular": {
        "food": {
            "title": "Build",
            "bullets": ["Colorful plants and steady protein.", "A good window to try new recipes."],
            "why": "Energy and appetite often stabilize.",
        },
        "activity": {
            "title": "Build capacity",
            "bullets": ["Strength or cardio may feel easier.", "Keep a rest day anyway."],
            "why": "Many people bounce back after bleeding eases.",
        },
        "mood": {
            "title": "Opening window",
            "bullets": ["Social plans can feel lighter.", "A good time to start something."],
            "why": "Mood often clears in this phase.",
        },
    },
    "ovulation": {
        "food": {
            "title": "Fuel the peak",
            "bullets": ["Greens, fiber, and omega-3s.", "Light meals if appetite dips."],
            "why": "A short peak, then a shift.",
        },
        "activity": {
            "title": "Peak window",
            "bullets": ["If they feel strong, skill sports fit.", "Ease off if they mention twinges."],
            "why": "Power can spike; so can pelvic awareness.",
        },
        "mood": {
            "title": "High signal",
            "bullets": ["Extra social energy is common.", "Still protect sleep."],
            "why": "Confidence and restlessness can both rise.",
        },
    },
    "luteal": {
        "food": {
            "title": "Steady",
            "bullets": ["Regular meals beat crash diets.", "Warm dinners if cravings hit."],
            "why": "Blood sugar can swing in the second half.",
        },
        "activity": {
            "title": "Taper",
            "bullets": ["Shorter sessions are fine.", "Walking or yoga over PRs."],
            "why": "Effort can feel higher than at ovulation.",
        },
        "mood": {
            "title": "Boundary and rest",
            "bullets": ["Shrink the to-do list.", "Don’t take a short fuse personally."],
            "why": "Sensitivity often rises before the next period.",
        },
    },
}

# Full owner copy (partner view) — keep in sync with frontend phaseContent.js
PARTNER_PANELS = {
    "menstrual": {
        "food": {
            "title": "Nourish and replenish",
            "bullets": [
                "Iron-rich meals: lentils, greens, or meat with citrus.",
                "Warm bowls: soups, stews, or oatmeal with seeds.",
                "Magnesium: dark chocolate, pumpkin seeds, banana.",
                "Stay hydrated; ginger or peppermint tea if it helps.",
            ],
            "why": "Blood loss can dip iron; rest and minerals matter more than restriction.",
        },
        "activity": {
            "title": "Gentle movement",
            "bullets": [
                "Walking, restorative yoga, or light stretching.",
                "Skip max-effort HIIT or heavy PRs if depleted.",
                "Pelvic tilts or child’s pose for lower-back ease.",
                "Sleep and warmth count as recovery training.",
            ],
            "why": "Lower energy makes high intensity harder; gentle movement still helps.",
        },
        "mood": {
            "title": "Soft awareness",
            "bullets": [
                "Expect a lower social battery; shorter plans are enough.",
                "Prefer journaling or a quiet playlist over packed nights.",
                "Heat pack and an early night if pain shows up.",
                "This dip is cyclic, not a character flaw.",
            ],
            "why": "Hormone withdrawal can flatten mood and raise pain sensitivity.",
        },
        "drive": {
            "title": "Comfort-first intimacy",
            "bullets": [
                "Desire may be quieter; “maybe later” is valid.",
                "Closeness without a goal: cuddling or slow massage.",
                "Side-lying or you-on-top so you control the pace.",
                "Use lube and patience if dryness or cramps appear.",
            ],
            "why": "Low estrogen can slow arousal; comfort beats performance.",
        },
    },
    "follicular": {
        "food": {
            "title": "Build and brighten",
            "bullets": [
                "Berries, cruciferous veg, and fermented foods.",
                "Protein plus complex carbs: eggs, yogurt, oats.",
                "Zinc and B-vitamins: seeds, grains, legumes.",
                "Try new recipes while appetite feels stable.",
            ],
            "why": "Rising estrogen often lifts energy and insulin sensitivity.",
        },
        "activity": {
            "title": "Build capacity",
            "bullets": [
                "Progressive strength, moderate cardio, or cycling.",
                "Practice new skills or intervals while recovery is easy.",
                "Keep a rest day; more energy is not no recovery.",
                "Take movement outdoors if daylight helps mood.",
            ],
            "why": "Climbing estrogen is linked with better strength and bounce-back.",
        },
        "mood": {
            "title": "Opening window",
            "bullets": [
                "Social plans and creative work often feel lighter.",
                "A good time for hard talks or starting a habit.",
                "Put extra focus into one priority, not ten.",
                "Notice confidence returning without forcing it.",
            ],
            "why": "Estrogen can support clearer mood after bleeding eases.",
        },
        "drive": {
            "title": "Curiosity and play",
            "bullets": [
                "Interest in sex or flirtation may pick up now.",
                "Try novelty: a new setting or slower build-up.",
                "Face-to-face or you-on-top for eye contact.",
                "Solo exploration is as valid as partnered play.",
            ],
            "why": "Rising estrogen often increases desire toward ovulation.",
        },
    },
    "ovulation": {
        "food": {
            "title": "Fuel the peak",
            "bullets": [
                "Fatty fish or walnuts, olive oil, and leafy greens.",
                "Fiber for extra estrogen: veg, beans, or flax.",
                "Light, frequent meals if appetite dips.",
                "Electrolytes if you are more active or warmer.",
            ],
            "why": "Estrogen peaks then falls; fiber and omega-3s support the shift.",
        },
        "activity": {
            "title": "Peak performance window",
            "bullets": [
                "If you feel strong: races, heavy lifts, or skill sports.",
                "Swap impact for swim or cycle if you get twinges.",
                "Shorter, sharper sessions beat long grinds.",
                "Cool down and mobilize hips after intense work.",
            ],
            "why": "The LH peak can coincide with higher power — and pelvic awareness.",
        },
        "mood": {
            "title": "High signal",
            "bullets": [
                "Extra social energy is common; still protect sleep.",
                "A good window for dates, talks, or collab work.",
                "If you feel wired, add a wind-down ritual.",
                "Track one feeling without judging it.",
            ],
            "why": "Peak estrogen can heighten confidence, attraction, and restlessness.",
        },
        "drive": {
            "title": "High-desire window",
            "bullets": [
                "Many people feel the strongest pull toward sex here.",
                "Say what you want early; energy can feel urgent.",
                "Playful positions: standing, from-behind, or you-on-top.",
                "This is the fertile window — use the protection you intend.",
            ],
            "why": "Ovulation often raises libido and lubrication; fertility is highest.",
        },
    },
    "luteal": {
        "food": {
            "title": "Steady the second half",
            "bullets": [
                "Magnesium and B6: greens, chickpeas, banana, seeds.",
                "Evening carbs if cravings hit: oats or sweet potato.",
                "Ease extra caffeine or alcohol if sleep suffers.",
                "Warm dinners; don’t crash-diet if you retain water.",
            ],
            "why": "Progesterone swings blood sugar; regular meals beat restriction.",
        },
        "activity": {
            "title": "Sustain, then taper",
            "bullets": [
                "Early luteal: keep moderate strength and cardio.",
                "Late luteal: yoga, walking, pilates, or shorter work.",
                "Deload if legs feel heavy or sleep is poor.",
                "Breath work or swimming if PMS tension shows up.",
            ],
            "why": "Progesterone can raise effort; what felt easy at ovulation may not.",
        },
        "mood": {
            "title": "Boundary and rest",
            "bullets": [
                "Irritability can spike; shrink the to-do list.",
                "Say no sooner and protect your evenings.",
                "Sharp monthly drops: ask a clinician about PMDD.",
                "Comfort rituals: bath, dim lights, fewer chats.",
            ],
            "why": "The premenstrual drop can heighten sensitivity; it is a phase.",
        },
        "drive": {
            "title": "Quality over urgency",
            "bullets": [
                "Desire may be mixed: closeness or space are both ok.",
                "Softer light, a longer warm-up, and extra lube.",
                "Spooning, pillow under hips, or slow you-on-top.",
                "Non-sexual touch still counts if orgasm feels far.",
            ],
            "why": "Progesterone dominates after ovulation; desire often eases.",
        },
    },
}


def panels_for_link(phase: str | None, link_type: str) -> dict | None:
    if not phase:
        return None
    if link_type == "partner":
        panels = PARTNER_PANELS.get(phase)
        if not panels:
            return None
        return {**panels, "support": PARTNER_SUPPORT.get(phase)}
    lite = FRIEND_LITE.get(phase)
    if not lite:
        return None
    return {**lite, "support": None}
