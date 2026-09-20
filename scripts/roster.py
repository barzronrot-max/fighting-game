"""Roster definitions for batch fighter generation (see batch-generate-roster.py)."""

# Visual description per character, written for image-gen prompts.
CHARACTERS: dict[str, str] = {
    "talon": (
        "a muscular humanoid eagle warrior. Brown feathered body with large folded brown-and-tan "
        "eagle wings on the back, a golden-brown eagle head with a hooked yellow beak and fierce "
        "amber eyes, two katana swords with blue-wrapped handles strapped in an X across the back, "
        "brown leather straps crossing the bare feathered chest, bronze-and-leather armored "
        "gauntlets and knee guards each set with a small red gem, tan-brown pants, powerful yellow "
        "taloned bird feet"
    ),
    "ryu": (
        "a disciplined Japanese karate master. White karate gi with rolled-up sleeves and frayed "
        "edges, a black belt, a red headband with tails flowing behind, short dark brown spiky "
        "hair, thick eyebrows, bare feet, red padded fighting gloves, strong athletic build"
    ),
    "kara": (
        "a female cyber-ninja assassin. Long flowing purple hair, a sleek black-and-purple skin-tight "
        "cyber bodysuit with glowing neon-purple circuit lines and armor plating on the shoulders "
        "and thighs, a utility belt with kunai knives, purple glowing eyes, black boots, slim agile build"
    ),
    "blaze": (
        "a male pyrokinetic brawler. Short red mohawk undercut hairstyle, a black leather vest with "
        "red trim worn open over a bare muscular chest, black combat pants with red flame patterns, "
        "black boots, fists wreathed in orange fire, a cocky grin, dog tags around the neck"
    ),
    "cyberon": (
        "a half-machine cyborg fighter. A shirtless muscular man whose entire left arm, left shoulder "
        "and left half of the torso are chrome-silver cybernetic machine parts with visible plating "
        "and cracks, a glowing red cybernetic left eye, short dark curly hair and a trimmed beard on "
        "the human right side, plain black training pants, black heavy boots"
    ),
    "shadow": (
        "a silent ninja assassin. Fully covered in a dark purple hooded ninja garb with a face mask "
        "showing only the eyes, a black tactical vest, a katana sheathed on the back, dark purple "
        "smoke wisps around the hands, black tabi boots, lean deadly build"
    ),
    "luna": (
        "a female ice sorceress fighter. Long flowing silver-white hair, a dark navy-blue skin-tight "
        "bodysuit with light-blue frost patterns and armored chest piece, ice-blue glowing eyes, "
        "frost mist around her hands, dark blue boots, athletic build, a short sword hilt over her shoulder"
    ),
    "titan": (
        "a colossal bald pit-fighter grappler. Enormous heavily-muscled build, shaved bald head with "
        "a thick neck and heavy brow, a brown leather chest harness with metal buckles crossing the "
        "bare torso, dark brown pants with a heavy belt, wrapped fists, big black boots, scars on the arms"
    ),
}

# Energy/effect color per character: (name for prompts, special tint, super tint)
ENERGY: dict[str, tuple[str, int, int]] = {
    "talon": ("white-and-tan razor wind", 0xf5f0e0, 0xf7e9c0),
    "ryu": ("blue-white ki", 0x93c5fd, 0x60a5fa),
    "kara": ("neon purple energy", 0xc084fc, 0xa855f7),
    "blaze": ("orange fire", 0xfb923c, 0xf97316),
    "cyberon": ("electric blue energy", 0x60a5fa, 0x3b82f6),
    "shadow": ("dark violet smoke energy", 0x8b5cf6, 0x7c3aed),
    "luna": ("ice-blue frost energy", 0xbae6fd, 0x7dd3fc),
    "titan": ("amber shockwave energy", 0xfbbf24, 0xb45309),
}

# Signature flavor for the cast / super poses.
SIGNATURE: dict[str, tuple[str, str]] = {
    "talon": (
        "hurling a slicing crescent of razor wind from one clawed hand",
        "spinning inside a raging tornado of wind and feathers, wings flared",
    ),
    "ryu": (
        "thrusting both palms forward launching a glowing blue-white ki sphere",
        "a rising dragon uppercut wreathed in blue-white ki flames",
    ),
    "kara": (
        "flinging a fan of glowing neon-purple kunai forward",
        "a blur of purple afterimages mid strike, neon energy trailing",
    ),
    "blaze": (
        "punching forward launching a roaring orange fireball",
        "engulfed in a towering inferno of orange flame, arms spread",
    ),
    "cyberon": (
        "firing a crackling blue energy beam from the chrome cybernetic arm",
        "overclocked, the whole body arcing with blue lightning, machine parts glowing",
    ),
    "shadow": (
        "throwing a dark violet smoke-wrapped shuriken forward",
        "mid shadow-execution slash, katana drawn, violet smoke exploding around",
    ),
    "luna": (
        "casting a spear of jagged ice forward from an open palm",
        "summoning a blizzard, ice crystals erupting from the ground around her",
    ),
    "titan": (
        "smashing a fist into the ground sending an amber shockwave forward",
        "roaring mid titan-crush double-hammerfist, amber energy cracking the air",
    ),
}

# FIGHTERS config values: (display name, spriteScale, tint, trim, accent, stats)
CONFIG: dict[str, tuple[str, float, int, int, int, list[int]]] = {
    "talon": ("TALON", 0.5, 0xb08428, 0xf2d270, 0x7a5f1e, [84, 88, 78]),
    "ryu": ("RYU", 0.5, 0xef4444, 0xfef3c7, 0xb91c1c, [80, 75, 90]),
    "kara": ("KARA", 0.46, 0xa855f7, 0xe9d5ff, 0x7e22ce, [70, 95, 85]),
    "blaze": ("BLAZE", 0.5, 0xf97316, 0xfed7aa, 0xc2410c, [85, 65, 60]),
    "cyberon": ("CYBERON", 0.5, 0x3b82f6, 0xbfdbfe, 0x1d4ed8, [85, 75, 80]),
    "shadow": ("SHADOW", 0.46, 0x7c3aed, 0xddd6fe, 0x5b21b6, [70, 95, 90]),
    "luna": ("LUNA", 0.46, 0x38bdf8, 0xe0f2fe, 0x0369a1, [70, 90, 85]),
    "titan": ("TITAN", 0.54, 0xb45309, 0xfde68a, 0x78350f, [120, 50, 60]),
}
