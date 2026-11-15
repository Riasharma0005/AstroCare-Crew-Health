"""Original poems by Ria Sharma. Stanzas are separated by a blank line."""

AUTHOR = "Ria Sharma"
COPYRIGHT = "Original poems by Ria Sharma."

POEMS = {
    "girl": dict(
        title="The Girl the Stars Remembered",
        mood="longing",
        text="""If I could hang a star
Each time you crossed my mind,
The cosmos would be jealous
Of the galaxy I'd design.

If the moon could count
The ounce of tears I shed,
Yearning for you every year,
It'd be watchful of you.

Only if you knew the times I screamed
Your name, as if it's the only way
To be saved.
It's a shame how you don't feel my love the same way.

The trees hear my whispers:
"Oh, she loves her lover like a poem,"
They quote as they whisper along,
And embrace it as a heavenly song.

He doesn't know me sometimes.
All he cares about is my demise.
Will his heart ache for me,
When my reflection is nowhere seen?

Or will the world keep spinning still,
Unmoved by where I've been,
While he forgets the girl who loved
Too deeply to be seen?""",
    ),
    "universe": dict(
        title="Am I the Universe?",
        mood="questioning",
        text="""People call it ethereal,
But the reality is unclear.
I look at the sky and the waves—
Am I the sailor of my life that sails?
Or am I just a passer by or a puppet, that fails?

Do we know the origin of life?
Or are we living on cues and lies?
Who's so mighty? I’ll fight
Till my inner world collides—
There exists a parallel universe?

I might question, or even doubt
Its origin... its all-about.
I see those stars sparkling at night,
But under the ocean, it screams demise.
Am I merely a part of it?
One in millions living beside.

Am I just a passer by? I wonder why
They call it ethereal and pretend—
Like we know its start and end.
Are we the players on a dashboard?
Or is it the universe playing us?

All of the choices that we make...
Should I keep quiet, or should I say—
The fates are entangled with our life.
Should I leave it all to fate?

Am I the universe of my life?
Will I fade or will I thrive?
Will I write my own fate?
Or is it too late?""",
    ),
    "stardust": dict(
        title="Stardust",
        mood="belonging",
        text="""Do I believe in life? Surely I do,
It's the cosmic attire woven through.
The undeniable fate, that I cross—
Isn't it already etched across?
I'm the stardust, once a star,
Blinked at night, distant & far.

I found myself in the physical laws,
Perfectly entangled with universal flaws.
The endless sky resonates with hope,
The depth of the sea— invites escape, a quiet elope.
This tingles a sensation in fingerprints,
How profoundly infused are the footprints?

The echoes of my consciousness whisper
Underlying truths, yet theories flicker.
The warmth of embrace that I know
Of the cosmic energy that silently flows.
Frequency synchronizes with comets,
Envelopes the undertone it sets.

I'm the stardust, once a star,
Residing with my kind, yet so far.
I belong in a cosmic life—
Wormhole, galaxy, or perhaps I might,
Travel with the speed of light.
Will I unite with a familiar ancestor,
Or might I discover a celestial visitor?

Hard to say, yet harder to hide,
I feel closer to the celestial tide.
The fear of the unknown, the horror it insists
How strange it is, to coexist.
I see the solace within my own eyes,
The stellar sea exists in paradise.

I'm the stardust, once the star,
Blinked at night, distant & far.""",
    ),
}

# Short excerpts (the author's own lines) used for "poem of the day" cards and breathing verses.
EXCERPTS = {
    "girl": ("If I could hang a star", "Each time you crossed my mind,"),
    "universe": ("Am I the universe of my life?", "Will I fade or will I thrive?"),
    "stardust": ("I'm the stardust, once a star,", "Blinked at night, distant & far."),
}
BREATH_VERSES = ["I'm the stardust, once a star,", "I feel closer to the celestial tide.",
                 "The stellar sea exists in paradise.", "Blinked at night, distant & far."]


def stanzas(key):
    return [s.split("\n") for s in POEMS[key]["text"].split("\n\n")]


def poem_for(ctx_level, low_contact):
    """Pick a poem to suggest from how the crew member is doing (gentle, never diagnostic)."""
    if low_contact:
        return "girl"
    if ctx_level == 2:
        return "universe"
    return "stardust"
