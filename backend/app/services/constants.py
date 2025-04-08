"""
Constants for question randomization in AI service.
This file contains data used to generate varied questions across different subjects and topics.
"""

# Student names representing diverse backgrounds and cultures
NAMES = [
    # Original names
    "Ava", "Noah", "Emma", "Liam", "Olivia", "Jackson", "Sophia", "Lucas", 
    "Mia", "Aiden", "Isabella", "Ethan", "Riley", "Elijah", "Aria", 
    "Grayson", "Amelia", "Mason", "Charlotte", "Logan", "Harper", "James",
    "Evelyn", "Alexander", "Abigail", "Michael", "Emily", "Benjamin", "Elizabeth", 
    "Zoe", "William", "Sofia", "Daniel", "Avery", "Matthew", "Scarlett", "Henry",
    "Victoria", "Sebastian", "Madison", "Jack", "Luna", "Owen", "Grace", "Isaiah",
    "Chloe", "Leo", "Penelope", "Ryan", "Layla", "Nathan", "Audrey",
    # Names with cultural diversity
    "Aisha", "Mohammed", "Fatima", "Omar", "Zara", "Ahmad", "Leila", "Hassan",
    "Priya", "Arjun", "Neha", "Raj", "Ananya", "Vikram", "Divya", "Rohan",
    "Wei", "Jing", "Li", "Ming", "Yan", "Chen", "Hui", "Xin",
    "Jamal", "Aaliyah", "DeShawn", "Imani", "Malik", "Zuri", "Xavier", "Nia",
    "Hiroshi", "Yuki", "Hana", "Kenji", "Aiko", "Takashi", "Mei", "Kazuki",
    "Santiago", "Isabella", "Mateo", "Valentina", "Diego", "Camila", "Alejandro", "Lucia",
    "Finn", "Saoirse", "Liam", "Niamh", "Cian", "Aoife", "Conor", "Siobhan",
    "Astrid", "Bjorn", "Freya", "Henrik", "Ingrid", "Lars", "Elsa", "Oskar",
    "Advik", "Kavya", "Dhruv", "Aanya", "Vihaan", "Ishani", "Reyansh", "Anaya",
    # Additional diverse names
    "Kaleb", "Amara", "Kwame", "Nia", "Kofi", "Zahara", "Jabari", "Zola", "Jelani", "Imani",
    "Pablo", "Elena", "Carlos", "Gabriela", "Rafael", "Sofia", "Eduardo", "Isidora", "Javier", "Carmen",
    "Akio", "Sakura", "Ryo", "Haruka", "Daiki", "Yuna", "Sora", "Ayumi", "Yuto", "Rin",
    "Amir", "Layla", "Tariq", "Amina", "Jamal", "Samira", "Yousef", "Nadia", "Karim", "Leila",
    "Ajay", "Zara", "Vivek", "Meera", "Rahul", "Anika", "Arnav", "Isha", "Vikram", "Tara",
    "Tao", "Xiu", "Feng", "Mei-Lin", "Jun", "Hui-Ying", "Bo", "Jia", "Chang", "An",
    "Olga", "Dmitri", "Anastasia", "Ivan", "Tatiana", "Mikhail", "Natalya", "Alexei", "Svetlana", "Nikolai",
    "Kwesi", "Ama", "Abena", "Kofi", "Efua", "Kwabena", "Esi", "Kwaku", "Akua", "Kojo",
    "Lakshmi", "Vijay", "Deepa", "Ajith", "Kavitha", "Rajiv", "Pooja", "Sunil", "Sarita", "Amit", 
    "Keya", "Kavya", "Riya", "Khush", "Tulsi", "Om", "Vansh", "Tanvi"
]

# Using full names list for math questions too
MATH_NAMES = NAMES

# Reading topics for comprehension questions
READING_TOPICS = [
    # Original topics
    "animals", "family", "school", "seasons", "weather", "space", 
    "ocean", "holidays", "food", "sports", "music", "art", 
    "nature", "travel", "community", "plants", "vehicles",
    "dinosaurs", "robots", "magic", "friendship", "pets", 
    "adventures", "insects", "birds", "camping", "cooking",
    "gardening", "jungle", "desert", "mountains", "inventions",
    "circus", "planets", "fairy tales", "superheroes", "dragons",
    # Additional topics
    "recycling", "environment", "different cultures", "history", "languages",
    "human body", "health", "emotions", "celebrations", "technology",
    "architecture", "engineering", "careers", "helpers", "transportation",
    "habitats", "endangered animals", "solar system", "astronomy", "chemistry",
    "physics", "biology", "geography", "countries", "continents", "oceans",
    "rivers", "lakes", "forests", "rainforests", "deserts", "arctic", "antarctic",
    "time", "measurement", "money", "shapes", "patterns", "colors", "senses",
    "festivals", "traditions", "mythology", "legends", "folktales", "biographies",
    "inventors", "scientists", "artists", "musicians", "writers", "athletes",
    "digital technology", "internet safety", "kindness", "responsibility", "teamwork",
    "problem-solving", "creativity", "imagination", "growth mindset", "mindfulness",
    # More educational topics
    "native cultures", "indigenous knowledge", "migration", "immigration", "cultural exchange",
    "natural resources", "sustainable development", "alternative energy", "climate change", "global warming",
    "marine life", "coral reefs", "tide pools", "deep sea creatures", "ocean conservation",
    "natural disasters", "earthquakes", "volcanoes", "hurricanes", "tsunamis", "erosion", "weathering",
    "life cycles", "metamorphosis", "adaptations", "evolution", "ecosystems", "food chains", "food webs",
    "simple machines", "forces and motion", "gravity", "friction", "magnetism", "electricity", "states of matter",
    "agriculture", "farming methods", "crop rotation", "composting", "irrigation", "hydroponics",
    "oral traditions", "storytelling", "puppetry", "theater history", "performance art", "mime", "dance forms",
    "poetry styles", "fiction genres", "non-fiction categories", "journalism", "publishing", "editing",
    "number systems", "currency", "ancient counting methods", "measurement systems", "calendar development",
    "map skills", "navigation methods", "cartography", "compass directions", "GPS technology",
    "digital literacy", "computer history", "programming basics", "virtual reality", "information privacy",
    "community service", "volunteerism", "activism", "charitable organizations", "social justice",
    "government systems", "democracy", "laws", "civic responsibility", "leadership", "conflict resolution",
    "disability awareness", "inclusivity", "universal design", "accessibility", "assistive technology",
    "world cuisines", "culinary traditions", "cooking methods", "nutrition", "food groups", "balanced diet",
    "textile arts", "weaving", "knitting", "sewing", "quilting", "embroidery", "fiber sources",
    "photography", "animation", "filmmaking", "documentary", "stop motion", "cinematography"
]

# Locations for reading passages
READING_LOCATIONS = [
    # Original locations
    "park", "home", "school", "garden", "beach", "forest", 
    "zoo", "playground", "library", "museum", "farm", 
    "neighborhood", "classroom", "kitchen", "backyard",
    "treehouse", "cave", "castle", "island", "mountain",
    "space station", "boat", "train", "airplane", "submarine",
    "aquarium", "amusement park", "campsite", "cottage",
    "desert", "jungle", "bakery", "hospital", "laboratory",
    # New locations
    "planetarium", "observatory", "greenhouse", "botanical garden", "wildlife reserve",
    "national park", "coral reef", "rainforest", "savanna", "grassland", "tundra",
    "community center", "theater", "art studio", "dance studio", "music room",
    "sports stadium", "swimming pool", "skating rink", "gymnasium", "fitness center",
    "archeological site", "historical monument", "ancient ruins", "medieval town",
    "space shuttle", "rocket", "helicopter", "hot air balloon", "sailboat", "cruise ship",
    "science center", "innovation hub", "maker space", "coding club", "robotics lab",
    "farmer's market", "shopping mall", "supermarket", "restaurant", "cafe", "food truck",
    "post office", "bank", "town hall", "courthouse", "police station", "fire station",
    "recycling center", "power plant", "wind farm", "solar park", "water treatment plant",
    "virtual reality world", "digital playground", "gaming arena", "esports center"
]

# Various elements to randomize math questions
MATH_OBJECTS = [
    # Original objects
    "apples", "oranges", "bananas", "pencils", "markers", "crayons", "books", "notebooks", 
    "cookies", "candies", "toys", "dolls", "cars", "blocks", "stickers", "coins", "marbles",
    "flowers", "plants", "trees", "dogs", "cats", "birds", "fish", "stickers", "cards",
    "erasers", "rulers", "paper clips", "buttons", "beads", "balls", "balloons", "cupcakes",
    # Additional objects
    "backpacks", "lunchboxes", "water bottles", "juice boxes", "granola bars", "sandwiches",
    "carrots", "celery sticks", "grapes", "strawberries", "blueberries", "pineapples",
    "mangoes", "kiwis", "watermelons", "lemons", "limes", "peaches", "plums", "cherries",
    "action figures", "stuffed animals", "board games", "puzzles", "video games", "trading cards",
    "comic books", "magazines", "chapter books", "picture books", "storybooks", "coloring books",
    "paintbrushes", "paint sets", "clay", "play-doh", "glitter", "sequins", "pipe cleaners",
    "construction paper", "scissors", "glue sticks", "tape dispensers", "staplers", "hole punchers",
    "quarters", "dimes", "nickels", "pennies", "dollar bills", "piggy banks", "wallets", "purses",
    "shirts", "pants", "dresses", "socks", "shoes", "hats", "scarves", "mittens", "gloves",
    "hamburgers", "hot dogs", "pizza slices", "tacos", "burritos", "sushi rolls", "pasta dishes",
    "ice cream cones", "popsicles", "donuts", "muffins", "croissants", "brownies", "lollipops",
    # More math objects
    "avocados", "radishes", "zucchinis", "eggplants", "cabbages", "broccoli", "cauliflower",
    "potatoes", "tomatoes", "cucumbers", "bell peppers", "mushrooms", "onions", "garlic",
    "tickets", "passes", "badges", "pins", "stickers", "patches", "medals", "trophies", "certificates",
    "bowling pins", "horseshoes", "darts", "dominoes", "playing cards", "poker chips", "dice",
    "postage stamps", "envelopes", "postcards", "greeting cards", "invitations", "stationery",
    "suitcases", "trunks", "luggage", "duffel bags", "backpacks", "messenger bags", "tote bags",
    "bricks", "tiles", "planks", "boards", "nails", "screws", "bolts", "nuts", "washers",
    "batteries", "light bulbs", "flashlights", "lanterns", "candles", "matches", "lighters",
    "musical notes", "measures", "beats", "rhythms", "melodies", "songs", "compositions",
    "years", "months", "weeks", "days", "hours", "minutes", "seconds", "decades", "centuries",
    "inches", "feet", "yards", "miles", "centimeters", "meters", "kilometers", "millimeters",
    "ounces", "pounds", "tons", "grams", "kilograms", "milligrams", "teaspoons", "tablespoons",
    "cups", "pints", "quarts", "gallons", "milliliters", "liters", "fluid ounces", "drops",
    "square inches", "square feet", "square yards", "square miles", "acres", "hectares",
    "equations", "problems", "expressions", "variables", "coefficients", "terms", "factors"
]

MATH_LOCATIONS = [
    # Original locations
    "store", "school", "park", "library", "home", "garden", "zoo", "farm", "beach", 
    "playground", "museum", "bakery", "party", "classroom", "bookstore", "market", "kitchen",
    "backyard", "basement", "garage", "attic", "treehouse", "clubhouse", "campsite", "amusement park",
    # New locations
    "community center", "sports arena", "swimming pool", "ice cream shop", "movie theater",
    "bowling alley", "arcade", "skating rink", "aquarium", "planetarium", "observatory",
    "science center", "art gallery", "concert hall", "dance studio", "music room", "gym",
    "cafeteria", "auditorium", "computer lab", "science lab", "greenhouse", "orchard",
    "vegetable garden", "flower shop", "pet store", "toy store", "candy shop", "food court",
    "restaurant", "cafe", "diner", "fast food place", "pizzeria", "sandwich shop", "taco stand",
    "birthday party", "holiday celebration", "family reunion", "school fair", "carnival",
    "circus", "parade", "festival", "talent show", "sports game", "field trip", "nature hike",
    "camping trip", "road trip", "vacation", "sleepover", "playdate", "picnic", "barbecue"
]

MATH_ACTIVITIES = [
    # Original activities
    "collecting", "buying", "sharing", "giving away", "selling", "counting", "finding", "arranging",
    "packing", "distributing", "sorting", "planting", "picking", "saving", "winning", "losing",
    "receiving", "dividing", "grouping", "organizing", "displaying", "gathering", "earning",
    # New activities
    "ordering", "shipping", "donating", "trading", "exchanging", "borrowing", "lending",
    "measuring", "weighing", "calculating", "estimating", "comparing", "matching", "categorizing",
    "classifying", "labeling", "stacking", "assembling", "building", "constructing", "creating",
    "designing", "drawing", "painting", "coloring", "decorating", "wrapping", "unwrapping",
    "delivering", "transporting", "moving", "carrying", "lifting", "pushing", "pulling",
    "loading", "unloading", "storing", "shelving", "arranging", "rearranging", "organizing",
    "collecting", "harvesting", "growing", "nurturing", "feeding", "watering", "trimming",
    "cutting", "slicing", "dividing", "separating", "combining", "mixing", "blending",
    "baking", "cooking", "preparing", "serving", "sharing", "distributing", "allocating"
]

MATH_WORD_PROBLEM_TEMPLATES = [
    # Original templates
    "{person} has {num1} {objects}. They {activity} {num2} more. How many {objects} do they have now?",
    "{person} had {num1} {objects}. They {activity} {num2} of them. How many {objects} do they have left?",
    "{person} and {person2} have {num1} and {num2} {objects} respectively. How many {objects} do they have in total?",
    "There are {num1} {objects} at the {location}. {person} brings {num2} more. How many {objects} are there now?",
    "{person} wants to share {num1} {objects} equally among {num2} friends. How many {objects} will each friend get?",
    "{person} has {num1} {objects} and {person2} has {num2} {objects}. How many more {objects} does {person} have?",
    "{person} arranges {num1} {objects} in {num2} equal rows. How many {objects} are in each row?",
    "{person} buys {num1} {objects} from the {location} for ${num2} each. How much money did {person} spend?",
    "If {person} collects {num1} {objects} each day, how many {objects} will {person} have after {num2} days?",
    "{person} has {num1} {objects}. {person2} has {num2} times as many. How many {objects} does {person2} have?",
    # New templates
    "{person} went to the {location} and bought {num1} {objects}. On the way home, they lost {num2} {objects}. How many {objects} do they have left?",
    "{person} and {person2} are {activity} {objects}. {person} has {num1} {objects} and {person2} has {num2} {objects}. How many {objects} do they have altogether?",
    "{person} is arranging {objects} in groups of {num1}. If they have {num2} {objects} in total, how many complete groups can they make?",
    "A {location} has {num1} {objects} for sale. If each customer can buy up to {num2} {objects}, how many customers can buy the maximum amount?",
    "{person} has a collection of {objects}. They organize them in {num1} rows with {num2} {objects} in each row. How many {objects} are there in total?",
    "{person} starts with {num1} {objects}. Every day, they {activity} {num2} more {objects}. How many {objects} will they have after 1 week?",
    "{person} and {num1} friends go to the {location}. If admission costs ${num2} per person, how much do they spend in total?",
    "{person} reads {num1} pages of a book each day. If the book has {num2} pages, how many days will it take to finish the book?",
    "{person} has {num1} boxes of {objects}. Each box contains {num2} {objects}. How many {objects} does {person} have in total?",
    "A class of {num1} students is divided into groups of {num2}. How many groups will there be?",
    "The {location} has {num1} {objects} that need to be packed in bags. Each bag can hold {num2} {objects}. How many bags are needed?",
    "{person} saved ${num1} per week for {num2} weeks. How much money did they save in total?",
    "{person} made {num1} {objects}. They gave {num2} to each friend and had 3 left over. How many friends received {objects}?",
    "{person} is {activity} {objects} at a rate of {num1} per hour. How many {objects} can they {activity} in {num2} hours?",
    "A recipe for {objects} requires {num1} cups of flour. If {person} wants to make {num2} batches, how many cups of flour are needed?",
    "{person} has ${num1} to spend on {objects}. If each {objects.slice(0,-1)} costs ${num2}, how many can {person} buy?",
    "The {location} is {num1} miles away. If {person} travels at {num2} miles per hour, how long will it take to get there?",
    "{person} needs {num1} {objects} for a project. They already have {num2} {objects}. How many more {objects} do they need to get?",
    "A {location} sells packages of {objects}. Each package has {num1} {objects}. How many packages should {person} buy to get at least {num2} {objects}?",
    "{person} wants to arrange {num1} {objects} in equal rows. If there are {num2} rows, how many {objects} will be in each row?"
]

MATH_WORD_PROBLEM_TEMPLATES += [
    # More advanced math problem templates
    "At the {location}, {person} noticed that there were {num1} {objects}. After some time, there were {num2} {objects}. How many {objects} had been added or removed?",
    "{person} and {person2} are collecting {objects}. {person} collects {num1} {objects} per hour, while {person2} collects {num2} {objects} per hour. How many {objects} will they collect together in 3 hours?",
    "{person} has {num1} {objects} to place in rows of {num2}. How many complete rows can be made, and how many {objects} will be left over?",
    "A {location} sells {objects} for ${num1} each or {num2} for ${num1 * num2 - (num2 * 0.5)}. How much money would {person} save by buying {num2} {objects}?",
    "In a game, {person} scores {num1} points for each {objects.slice(0,-1)}. If they collected {num2} {objects}, how many points did they score?",
    "{person} needs to fill {num1} containers with {objects}. Each container holds {num2} {objects}. How many more {objects} does {person} need to buy to fill all containers?",
    "At the beginning of the week, {person} had {num1} {objects}. By the end of the week, the number had doubled. How many {objects} did {person} have at the end of the week?",
    "{person} is making a pattern with {objects}. For every {num1} red {objects}, there are {num2} blue {objects}. If {person} uses {num1 * 3} red {objects}, how many blue {objects} will be in the pattern?",
    "{person} and {person2} have a total of {num1} {objects}. If {person} has {num2} {objects}, how many {objects} does {person2} have?",
    "For a craft project, {person} needs {num1} {objects}. These are sold in packs of {num2}. What is the minimum number of packs {person} needs to buy?",
    "At the {location}, {person} sees that {objects} cost ${num1} each. If {person} has ${num2}, what is the maximum number of {objects} that can be purchased?",
    "{person} walks {num1} miles per hour. How long will it take {person} to walk {num2} miles?",
    "If {num1} {objects} cost ${num2}, what is the cost of one {objects.slice(0,-1)}?",
    "{person} spends {num1} minutes each day {activity} {objects}. How many hours does {person} spend {activity} {objects} in one week?",
    "The {location} has {num1} {objects} divided equally among {num2} containers. How many {objects} are in each container?",
    "{person} jumped rope {num1} times on Monday, {num1 + 5} times on Tuesday, and {num1 + 10} times on Wednesday. How many total jumps did {person} do?",
    "{person}'s goal is to {activity} {num1} {objects}. If {person} has already {activity} {num2} {objects}, how many more {objects} need to be {activity} to reach the goal?",
    "A recipe calls for {num1} cups of flour to make {num2} cookies. How many cups of flour are needed to make 1 cookie?",
    "{person} has a collection of {objects} that weighs {num1} pounds. If each {objects.slice(0,-1)} weighs {num2} ounces, how many {objects} are in the collection? (16 ounces = 1 pound)",
    "The temperature on Monday was {num1} degrees. On Tuesday, it dropped by {num2} degrees. What was the temperature on Tuesday?"
]

# English randomization elements
ENGLISH_TOPICS = [
    # Original topics
    "animals", "plants", "weather", "seasons", "family", "friends", "school", "sports",
    "hobbies", "food", "travel", "colors", "shapes", "vehicles", "clothes", "emotions",
    "celebrations", "movies", "music", "books", "nature", "planets", "oceans", "mountains",
    "insects", "dinosaurs", "community helpers", "transportation", "outer space", "zoo animals",
    "farm animals", "pets", "fairy tales", "superheroes", "holidays", "art", "science", "history",
    # New topics
    "ecology", "environment", "conservation", "recycling", "renewable energy", "sustainability",
    "cultural diversity", "world languages", "global citizenship", "digital citizenship",
    "internet safety", "cyber security", "coding", "robotics", "artificial intelligence",
    "virtual reality", "augmented reality", "3D printing", "engineering", "architecture",
    "civil engineering", "mechanical engineering", "electrical engineering", "chemical engineering",
    "astronomy", "astrophysics", "cosmology", "space exploration", "mars colonization",
    "human body", "anatomy", "physiology", "health", "nutrition", "exercise", "mental health",
    "mindfulness", "well-being", "emotions", "emotional intelligence", "social skills",
    "communication", "collaboration", "teamwork", "leadership", "entrepreneurship", "innovation",
    "creativity", "problem-solving", "critical thinking", "design thinking", "maker movement",
    "ancient civilizations", "world history", "local history", "cultural heritage", "archaeology",
    "paleontology", "geology", "meteorology", "oceanography", "marine biology", "zoology", "botany"
]

ENGLISH_VERBS = [
    # Original verbs
    "run", "jump", "swim", "play", "read", "write", "draw", "paint", "sing", "dance",
    "eat", "drink", "sleep", "walk", "talk", "laugh", "smile", "cry", "help", "watch",
    "listen", "speak", "work", "study", "learn", "teach", "make", "build", "create", "find",
    "explore", "discover", "climb", "fly", "throw", "catch", "kick", "push", "pull", "ride",
    "drive", "visit", "grow", "plant", "cook", "bake", "clean", "wash", "fold", "carry",
    # New verbs
    "analyze", "investigate", "experiment", "observe", "collect", "gather", "organize", "categorize",
    "classify", "sort", "compare", "contrast", "measure", "calculate", "estimate", "predict",
    "hypothesize", "test", "prove", "conclude", "summarize", "explain", "describe", "define",
    "illustrate", "demonstrate", "present", "perform", "act", "direct", "produce", "compose",
    "design", "sketch", "craft", "construct", "assemble", "invent", "innovate", "improve",
    "modify", "adapt", "adjust", "fix", "repair", "maintain", "preserve", "protect", "conserve",
    "recycle", "reduce", "reuse", "share", "distribute", "allocate", "assign", "delegate",
    "collaborate", "cooperate", "assist", "support", "encourage", "motivate", "inspire",
    "lead", "guide", "direct", "instruct", "advise", "suggest", "recommend", "consult",
    "communicate", "express", "articulate", "convey", "translate", "interpret", "decode", "encode",
    "program", "code", "debug", "upload", "download", "install", "configure", "customize"
]

ENGLISH_ADJECTIVES = [
    # Original adjectives
    "happy", "sad", "big", "small", "fast", "slow", "hot", "cold", "new", "old",
    "good", "bad", "easy", "hard", "funny", "serious", "loud", "quiet", "clean", "dirty",
    "bright", "dark", "soft", "hard", "sweet", "sour", "tall", "short", "strong", "weak",
    "brave", "scared", "kind", "mean", "pretty", "ugly", "smart", "silly", "friendly", "shy",
    "young", "smooth", "rough", "shiny", "dull", "heavy", "light", "thick", "thin", "sharp",
    # New adjectives
    "amazing", "wonderful", "fantastic", "terrific", "awesome", "excellent", "magnificent",
    "brilliant", "clever", "intelligent", "thoughtful", "creative", "imaginative", "innovative",
    "curious", "inquisitive", "adventurous", "daring", "courageous", "fearless", "bold", "brave",
    "cautious", "careful", "gentle", "soft", "delicate", "fragile", "sturdy", "solid", "firm",
    "flexible", "rigid", "elastic", "stretchy", "sticky", "slippery", "sleek", "fluffy", "fuzzy",
    "furry", "feathery", "scaly", "smooth", "bumpy", "prickly", "pointy", "curved", "straight",
    "flat", "round", "square", "triangular", "rectangular", "cylindrical", "spherical", "cubic",
    "gigantic", "enormous", "huge", "massive", "tiny", "miniature", "microscopic", "colossal",
    "spacious", "cramped", "narrow", "wide", "deep", "shallow", "high", "low", "towering",
    "transparent", "opaque", "translucent", "clear", "foggy", "misty", "cloudy", "stormy",
    "sunny", "rainy", "windy", "snowy", "icy", "frosty", "steamy", "humid", "dry", "moist",
    "noisy", "silent", "melodic", "harmonious", "rhythmic", "cacophonous", "peaceful", "chaotic",
    "orderly", "messy", "organized", "scattered", "aligned", "crooked", "symmetrical", "balanced"
]

ENGLISH_NOUNS = [
    # Original nouns
    "dog", "cat", "bird", "fish", "tree", "flower", "house", "car", "book", "toy",
    "ball", "game", "chair", "table", "bed", "door", "window", "phone", "computer", "school",
    "friend", "family", "teacher", "student", "doctor", "police", "firefighter", "park", "store", "zoo",
    "mountain", "river", "ocean", "beach", "forest", "cake", "cookie", "ice cream", "pizza", "sandwich",
    # New nouns
    "astronaut", "scientist", "engineer", "artist", "musician", "author", "chef", "athlete", "actor",
    "dancer", "programmer", "designer", "architect", "veterinarian", "gardener", "farmer", "builder",
    "inventor", "explorer", "detective", "photographer", "filmmaker", "journalist", "pilot", "sailor",
    "robot", "dinosaur", "volcano", "earthquake", "tornado", "hurricane", "galaxy", "planet", "star",
    "satellite", "rocket", "spaceship", "telescope", "microscope", "laboratory", "experiment", "invention",
    "discovery", "museum", "library", "theater", "stadium", "arena", "concert", "exhibition", "festival",
    "celebration", "holiday", "birthday", "anniversary", "graduation", "ceremony", "parade", "carnival",
    "amusement park", "playground", "skatepark", "water park", "aquarium", "planetarium", "observatory",
    "classroom", "gymnasium", "cafeteria", "auditorium", "hallway", "office", "studio", "workshop",
    "garden", "orchard", "meadow", "prairie", "desert", "rainforest", "tundra", "savanna", "reef",
    "canyon", "valley", "plateau", "peninsula", "island", "continent", "country", "city", "town",
    "village", "neighborhood", "community", "society", "culture", "tradition", "history", "future"
]

ENGLISH_WORD_PATTERNS = [
    # Original patterns
    "Synonyms - words that mean the same as '{word}'",
    "Antonyms - words that mean the opposite of '{word}'",
    "Words that rhyme with '{word}'",
    "Words that start with the same letter as '{word}'",
    "Compound words that include '{word}'",
    "The correct spelling of '{word}'",
    "The plural form of '{word}'",
    "The past tense of '{word}'",
    "The correct definition of '{word}'",
    "Identifying '{word}' as a noun/verb/adjective",
    # New patterns
    "Words in the same category as '{word}'",
    "Adding a prefix to '{word}' to create a new word",
    "Adding a suffix to '{word}' to create a new word",
    "Breaking the compound word '{word}' into its parts",
    "Words that have the same vowel sound as '{word}'",
    "The root word of '{word}'",
    "Words derived from the root word in '{word}'",
    "The singular form of '{word}'",
    "The future tense of '{word}'",
    "The present participle form of '{word}'",
    "The comparative form of '{word}'",
    "The superlative form of '{word}'",
    "Homophones for '{word}'",
    "Homographs for '{word}'",
    "The syllables in '{word}'",
    "The part of speech for '{word}' in this sentence",
    "The meaning of the idiom containing '{word}'",
    "A simile using '{word}'",
    "A metaphor using '{word}'",
    "An alliteration using '{word}'",
    "Words that contain the same root as '{word}'"
]

ENGLISH_GRAMMAR_TEMPLATES = [
    # Original templates
    "Which sentence uses the correct form of '{verb}'?",
    "Which sentence has the correct punctuation?",
    "Which word is a {part_of_speech}?",
    "Fill in the blank: '{sentence_start} _____ {sentence_end}'",
    "Which sentence is grammatically correct?",
    "Which word should come next in this sentence: '{sentence}'",
    "What is the correct article (a/an/the) to use with '{noun}'?",
    "What is the correct prefix to use with '{word}' to mean '{meaning}'?",
    "What is the correct suffix to add to '{word}' to make it '{desired_form}'?",
    "Which sentence uses '{word}' correctly?",
    # New templates
    "Choose the correct pronoun: '{sentence_start} _____ {sentence_end}'",
    "Which sentence uses the correct verb tense?",
    "Identify the subject in this sentence: '{sentence}'",
    "Identify the predicate in this sentence: '{sentence}'",
    "Identify the direct object in this sentence: '{sentence}'",
    "Identify the indirect object in this sentence: '{sentence}'",
    "Which sentence uses the correct plural form?",
    "Which sentence uses the correct possessive form?",
    "Which sentence uses the correct comparative adjective?",
    "Which sentence uses the correct superlative adjective?",
    "Choose the correct conjunction to join these sentences: '{sentence1}' and '{sentence2}'",
    "Identify the preposition in this sentence: '{sentence}'",
    "Which sentence contains a compound subject?",
    "Which sentence contains a compound predicate?",
    "Which sentence is in the active voice?",
    "Which sentence is in the passive voice?",
    "What is the correct way to combine these sentences? '{sentence1}' and '{sentence2}'",
    "Which sentence uses correct subject-verb agreement?",
    "What is the correct word order in this sentence? {scrambled_sentence}",
    "Identify the independent clause in this sentence: '{sentence}'",
    "Identify the dependent clause in this sentence: '{sentence}'",
    "Which punctuation mark should go in the blank? '{sentence_part1} __ {sentence_part2}'",
    "Which sentence demonstrates parallel structure?",
    "What type of sentence is this: '{sentence}'? (declarative, interrogative, imperative, exclamatory)",
    "Choose the correct form of the irregular verb: '{sentence_start} _____ {sentence_end}'"
]

ENGLISH_GRAMMAR_TEMPLATES += [
    # Advanced grammar templates
    "Which sentence demonstrates the correct use of the subjunctive mood?",
    "Identify the gerund phrase in this sentence: '{sentence}'",
    "Which sentence contains an infinitive phrase?",
    "Identify the participial phrase in this sentence: '{sentence}'",
    "Which sentence uses a relative pronoun correctly?",
    "Identify the adverbial clause in this sentence: '{sentence}'",
    "Which sentence demonstrates correct parallel structure in a list?",
    "Identify the appositive phrase in this sentence: '{sentence}'",
    "Which sentence correctly uses a semicolon?",
    "Identify the noun clause in this sentence: '{sentence}'",
    "Which sentence demonstrates correct subject-verb agreement with collective nouns?",
    "In the sentence '{sentence}', what is the function of the italicized phrase?",
    "Which revision best combines these sentences into a compound-complex sentence?",
    "Which sentence correctly uses correlative conjunctions?",
    "Identify the type of conditional statement in this sentence: '{sentence}'",
    "Which sentence correctly uses the past perfect tense?",
    "In this sentence '{sentence}', what type of modifier is the underlined word?",
    "Which sentence correctly uses a colon?",
    "Identify the nominative absolute phrase in this sentence: '{sentence}'",
    "Which revision corrects the dangling modifier in this sentence?"
]

# Scenarios for enhanced grammar correction randomization
SCENARIOS = [
    # Original scenarios
    "playing at the park", "visiting the zoo", "reading in the library",
    "working on a science project", "helping in the garden", "baking cookies",
    "building a sandcastle", "drawing a picture", "solving a math problem",
    "writing a story", "practicing piano", "feeding the fish", "walking the dog",
    "riding a bicycle", "swimming in the pool", "making a craft", "going on a hike",
    "shopping at the grocery store", "celebrating a birthday", "visiting grandparents",
    "cleaning their room", "planting flowers", "watching a movie", "playing soccer",
    "building with blocks", "singing in the choir", "eating lunch", "taking a test",
    "going camping", "flying a kite", "collecting leaves", "looking at stars",
    "playing video games", "writing a letter", "making a sandwich", "painting a picture",
    "playing basketball", "doing homework", "telling a joke", "learning an instrument",
    "folding laundry", "walking to school", "riding the bus", "playing with friends",
    "sharing toys", "helping a teacher", "taking care of a pet", "jumping rope",
    "playing board games", "exploring a museum",
    # New scenarios
    "programming a robot", "designing a video game", "creating a website", "editing a video",
    "recording a podcast", "filming a movie", "acting in a play", "dancing in a recital",
    "competing in a spelling bee", "participating in a science fair", "entering an art contest",
    "publishing a school newspaper", "organizing a book club", "leading a study group",
    "planting a community garden", "volunteering at an animal shelter", "cleaning up a park",
    "recycling materials", "conserving water", "reducing energy usage", "composting food waste",
    "growing vegetables", "harvesting fruits", "cooking a meal", "baking bread", "making jam",
    "designing a model", "building a birdhouse", "constructing a miniature bridge", "assembling a puzzle",
    "creating a diorama", "drawing a map", "charting a constellation", "tracking weather patterns",
    "measuring rainfall", "observing plant growth", "documenting animal behavior", "collecting specimens",
    "conducting an experiment", "taking a field trip", "visiting a nature center", "exploring a cave",
    "hiking a trail", "climbing a mountain", "rafting down a river", "canoeing across a lake",
    "setting up a tent", "building a campfire", "identifying birds", "spotting wildlife",
    "learning a new language", "practicing sign language", "writing in a journal", "composing a poem",
    "designing a greeting card", "creating origami", "weaving a basket", "knitting a scarf",
    "sewing a pillow", "making jewelry", "carving soap", "crafting pottery", "sculpting with clay",
    "performing in a talent show", "playing in a band", "singing in a chorus", "joining an orchestra",
    "creating a podcast", "designing an app", "making a digital art portfolio", "coding a simple game",
    "launching a model rocket", "constructing a weather station", "building an earthquake simulator",
    "making stop-motion animation", "designing a board game", "creating a comic book series",
    "writing a choose-your-own-adventure story", "compiling a family cookbook", "designing fashion",
    "researching endangered species", "starting a neighborhood cleanup", "planting a butterfly garden",
    "tracking satellite movements", "observing lunar phases", "mapping constellations", "measuring shadows",
    "designing an accessible playground", "creating tactile art", "developing a sign language dictionary",
    "inventing a new musical instrument", "composing a song", "choreographing a dance", "directing a play",
    "engineering a bridge from recycled materials", "creating a water filtration system", "building a solar oven",
    "designing a sustainable house", "planning a community garden", "mapping a neighborhood", "surveying biodiversity",
    "planning a space colony", "designing a rover", "creating a new sport", "inventing exercise equipment",
    "cooking a dish from another culture", "learning ancestral recipes", "starting a cultural exchange",
    "creating a time capsule", "developing a family tree", "documenting oral histories", "preserving traditions",
    "starting a school newspaper", "hosting a radio show", "creating a photo essay", "filming a documentary",
    "designing adaptive equipment", "developing assistive technology", "writing in braille", "learning tactile sign language"
]

# Objects that can be used in sentences
OBJECTS = [
    # Original objects
    "book", "ball", "pencil", "apple", "backpack", "toy", "bicycle", "computer",
    "sandwich", "painting", "puzzle", "kite", "rock", "flower", "tree", "hat",
    "cup", "box", "shoe", "game", "picture", "notebook", "crayon", "tablet",
    "chair", "desk", "blocks", "doll", "truck", "markers", "glue", "scissors",
    # New objects
    "telescope", "microscope", "binoculars", "magnifying glass", "compass", "map",
    "globe", "atlas", "dictionary", "thesaurus", "encyclopedia", "yearbook", "almanac",
    "guidebook", "manual", "textbook", "workbook", "sketchbook", "scrapbook", "journal",
    "diary", "poster", "blueprint", "diagram", "chart", "graph", "model", "prototype",
    "sculpture", "ceramics", "pottery", "mosaic", "collage", "origami", "quilt", "banner",
    "instrument", "guitar", "piano", "violin", "trumpet", "flute", "recorder", "drum",
    "xylophone", "tambourine", "maraca", "triangle", "cymbal", "keyboard", "microphone",
    "camera", "video camera", "tripod", "projector", "screen", "headphones", "speakers",
    "calculator", "ruler", "protractor", "compass", "scale", "stopwatch", "timer", "clock",
    "calendar", "planner", "organizer", "clipboard", "bulletin board", "whiteboard", "chalkboard",
    "robot", "drone", "remote control car", "walkie-talkie", "telescope", "rocket", "kite",
    "frisbee", "jump rope", "hula hoop", "yo-yo", "slinky", "playing cards", "dice", "chess set",
    "harmonica", "kazoo", "bongos", "castanet", "ocarina", "kalimba", "ukulele", "lyre", "harp",
    "kaleidoscope", "periscope", "sundial", "prism", "abacus", "metronome", "gyroscope",
    "hour glass", "barometer", "pedometer", "solar panel", "wind turbine", "weather vane",
    "stethoscope", "telescope", "periscope", "seismograph", "microscope", "magnifying glass",
    "constellation chart", "star map", "globe", "topographical map", "physical map", "atlas",
    "terrarium", "aquarium", "bonsai", "succulent", "cactus", "seedling", "sapling",
    "bookmark", "calligraphy pen", "quill", "parchment", "scroll", "manuscript", "tablet",
    "easel", "pottery wheel", "spinning wheel", "loom", "mortar and pestle", "rolling pin",
    "mason jar", "test tube", "beaker", "graduated cylinder", "petri dish", "specimen container",
    "field guide", "identification key", "compass", "binoculars", "spotting scope", "trail marker",
    "3D printer", "circuit board", "microcontroller", "LED light", "sensor", "motor", "battery pack",
    "virtual reality headset", "augmented reality glasses", "hologram projector", "motion sensor"
]

# Settings/locations for contextual variety
LOCATIONS = [
    # Original locations
    "classroom", "playground", "home", "library", "park", "beach", "museum",
    "aquarium", "zoo", "garden", "kitchen", "cafeteria", "gymnasium", "art room",
    "backyard", "treehouse", "swimming pool", "farm", "forest", "shopping mall",
    "school bus", "soccer field", "birthday party", "science lab", "music room",
    # New locations
    "maker space", "computer lab", "coding club", "robotics workshop", "engineering lab",
    "media center", "broadcasting studio", "recording booth", "green screen room", "stage",
    "auditorium", "theater", "performing arts center", "rehearsal space", "dance studio",
    "sports arena", "track and field", "basketball court", "baseball diamond", "football field",
    "hockey rink", "tennis court", "skate park", "climbing wall", "obstacle course",
    "nature center", "botanical garden", "arboretum", "wildlife sanctuary", "butterfly garden",
    "planetarium", "observatory", "science center", "innovation hub", "discovery zone",
    "history museum", "art gallery", "children's museum", "cultural center", "heritage site",
    "community garden", "recycling center", "farmers market", "food pantry", "animal shelter",
    "fire station", "police station", "post office", "city hall", "courthouse", "hospital",
    "doctor's office", "dental clinic", "veterinary clinic", "pharmacy", "health center",
    "bookstore", "comic book shop", "toy store", "craft store", "hobby shop", "electronics store",
    "bakery", "ice cream parlor", "pizza place", "cafe", "restaurant", "food truck", "diner",
    "movie theater", "bowling alley", "arcade", "mini golf course", "water park", "theme park"
]

# Time expressions for adding temporal context
TIME_EXPRESSIONS = [
    # Original expressions
    "yesterday", "last week", "this morning", "after school", "during recess",
    "before dinner", "on the weekend", "last summer", "every day", "tomorrow",
    "next week", "at night", "in the afternoon", "on Monday", "during lunch",
    # New expressions
    "last night", "this evening", "early morning", "late afternoon", "at sunrise",
    "at sunset", "at dawn", "at dusk", "at midnight", "at noon", "in the evening",
    "during breakfast", "after breakfast", "before lunch", "after lunch", "during dinner",
    "after dinner", "before bedtime", "during naptime", "after class", "before class",
    "between classes", "during art class", "during music class", "during gym class",
    "during science class", "during math class", "during reading time", "during quiet time",
    "on Tuesday", "on Wednesday", "on Thursday", "on Friday", "on Saturday", "on Sunday",
    "on a weekday", "on a weekend", "on a holiday", "on vacation", "on a field trip",
    "in January", "in February", "in March", "in April", "in May", "in June",
    "in July", "in August", "in September", "in October", "in November", "in December",
    "in winter", "in spring", "in summer", "in fall", "during winter break", "during spring break",
    "during summer vacation", "during the school year", "at the beginning of the year",
    "at the end of the year", "at the start of class", "at the end of class",
    "while studying", "while playing", "while reading", "while writing", "while listening",
    "after finishing homework", "before starting homework", "while working on a project"
]

# New category: Science experiment vocabulary
SCIENCE_VOCABULARY = [
    "hypothesis", "experiment", "observation", "conclusion", "data", "variable", "control", 
    "independent variable", "dependent variable", "analysis", "results", "evidence",
    "prediction", "inquiry", "investigation", "procedure", "method", "sample", "specimen",
    "microscope", "telescope", "thermometer", "scale", "meter", "test tube", "beaker",
    "graduated cylinder", "safety goggles", "lab coat", "forceps", "pipette", "magnifying glass",
    "petri dish", "slide", "coverslip", "burner", "flame", "heat", "temperature", "freeze",
    "boil", "evaporate", "condense", "dissolve", "solution", "mixture", "compound", "element",
    "atom", "molecule", "cell", "tissue", "organ", "system", "organism", "ecosystem",
    "life cycle", "metamorphosis", "adaptation", "evolution", "genetics", "inheritance",
    "photosynthesis", "respiration", "germination", "pollination", "decomposition",
    "weather", "climate", "atmosphere", "humidity", "precipitation", "erosion", "geology",
    "mineral", "rock", "fossil", "sediment", "core", "crust", "mantle", "plate tectonics",
    "force", "motion", "energy", "momentum", "friction", "gravity", "magnetism", "electricity",
    "circuit", "conductor", "insulator", "battery", "solar", "renewable", "conservation",
    "solid", "liquid", "gas", "plasma", "matter", "mass", "weight", "density", "volume",
    "pressure", "sound", "light", "spectrum", "reflection", "refraction", "transparency"
]

# New category: Math vocabulary
MATH_VOCABULARY = [
    "add", "subtract", "multiply", "divide", "equals", "sum", "difference", "product", "quotient",
    "fraction", "decimal", "percent", "numerator", "denominator", "equivalent", "improper", "mixed number",
    "place value", "digit", "ones", "tens", "hundreds", "thousands", "round", "estimate", "regroup",
    "number line", "greater than", "less than", "equal to", "compare", "order", "sequence", "pattern",
    "odd", "even", "prime", "composite", "factor", "multiple", "divisible", "remainder", "divisor",
    "array", "row", "column", "grid", "coordinate", "axis", "x-axis", "y-axis", "origin", "quadrant",
    "point", "line", "ray", "angle", "degree", "vertex", "acute", "obtuse", "right", "straight",
    "plane", "shape", "polygon", "triangle", "quadrilateral", "pentagon", "hexagon", "octagon",
    "circle", "radius", "diameter", "circumference", "center", "arc", "sphere", "cube", "rectangular prism",
    "cylinder", "cone", "pyramid", "face", "edge", "vertex", "base", "height", "net", "solid",
    "perimeter", "area", "volume", "square unit", "cubic unit", "length", "width", "height", "distance",
    "symmetry", "reflection", "rotation", "translation", "congruent", "similar", "scale", "proportion",
    "probability", "certain", "likely", "unlikely", "impossible", "outcome", "event", "random", "chance",
    "data", "graph", "chart", "table", "bar graph", "pictograph", "line plot", "pie chart", "histogram",
    "mean", "median", "mode", "range", "minimum", "maximum", "frequency", "survey", "tally", "predict",
    "algebra", "variable", "expression", "equation", "inequality", "evaluate", "solve", "balance",
    "time", "elapsed time", "calendar", "schedule", "hour", "minute", "second", "money", "cent", "dollar"
]

# New category: Computer science vocabulary for kids
COMPUTER_VOCABULARY = [
    "computer", "laptop", "tablet", "smartphone", "desktop", "monitor", "screen", "keyboard", "mouse",
    "trackpad", "touchscreen", "speaker", "headphones", "microphone", "camera", "printer", "scanner",
    "hardware", "software", "program", "app", "application", "game", "website", "internet", "online",
    "offline", "download", "upload", "save", "file", "folder", "document", "photo", "video", "audio",
    "click", "double-click", "right-click", "drag", "drop", "scroll", "swipe", "tap", "type", "input",
    "output", "data", "information", "password", "username", "login", "account", "profile", "avatar",
    "icon", "menu", "window", "tab", "button", "link", "cursor", "pointer", "emoji", "sticker",
    "search", "browse", "navigate", "bookmark", "favorite", "history", "settings", "preferences",
    "code", "programming", "algorithm", "sequence", "loop", "condition", "function", "command",
    "robot", "debug", "error", "bug", "fix", "test", "run", "execute", "compile", "binary",
    "pixel", "resolution", "graphic", "animation", "3D", "virtual reality", "augmented reality", 
    "simulation", "model", "design", "create", "edit", "delete", "copy", "paste", "cut", "undo", "redo",
    "wifi", "bluetooth", "network", "connection", "server", "cloud", "storage", "backup", "sync",
    "email", "message", "chat", "video call", "share", "post", "comment", "like", "follow", "subscribe",
    "security", "privacy", "protect", "virus", "malware", "firewall", "update", "version", "install",
    "digital", "electronic", "technology", "device", "gadget", "smart", "memory", "battery", "charge",
    "power", "start", "restart", "shut down", "sleep", "wake", "freeze", "crash", "loading"
]

# New category: Historical periods for kids
HISTORICAL_PERIODS = [
    "prehistoric times", "stone age", "bronze age", "iron age", "ancient Egypt", "ancient Greece",
    "ancient Rome", "ancient China", "ancient India", "ancient Maya", "ancient Aztecs", "ancient Incas",
    "Vikings", "Middle Ages", "medieval times", "knights and castles", "Renaissance", "exploration age",
    "American Revolution", "French Revolution", "Industrial Revolution", "Victorian era", "World War I",
    "Roaring Twenties", "Great Depression", "World War II", "Cold War", "Space Age", "Civil Rights Movement",
    "Digital Age", "21st century", "colonial times", "pioneer days", "Wild West", "Gold Rush",
    "dinosaur era", "Ice Age", "Jurassic period", "Cretaceous period", "Triassic period", "cavemen days",
    "pharaohs and pyramids", "gladiators and coliseums", "samurai era", "pirate times", "American frontier",
    "immigrant journeys", "Native American history", "African kingdoms", "European monarchy", "Asian dynasties",
    "Latin American independence", "Australian settlement", "Arctic exploration", "desert civilizations",
    "river valley civilizations", "maritime empires", "trading routes", "silk road", "spice trade",
    "agricultural revolution", "writing invention", "printing press era", "telephone invention",
    "automobile age", "flight invention", "television era", "computer revolution", "internet beginning",
    "smartphone era", "social media age", "space exploration", "moon landing", "Mars rovers"
]

# Expanded scenarios for enhanced grammar correction randomization
SCENARIOS += [
    "creating a podcast", "designing an app", "making a digital art portfolio", "coding a simple game",
    "launching a model rocket", "constructing a weather station", "building an earthquake simulator",
    "making stop-motion animation", "designing a board game", "creating a comic book series",
    "writing a choose-your-own-adventure story", "compiling a family cookbook", "designing fashion",
    "researching endangered species", "starting a neighborhood cleanup", "planting a butterfly garden",
    "tracking satellite movements", "observing lunar phases", "mapping constellations", "measuring shadows",
    "designing an accessible playground", "creating tactile art", "developing a sign language dictionary",
    "inventing a new musical instrument", "composing a song", "choreographing a dance", "directing a play",
    "engineering a bridge from recycled materials", "creating a water filtration system", "building a solar oven",
    "designing a sustainable house", "planning a community garden", "mapping a neighborhood", "surveying biodiversity",
    "planning a space colony", "designing a rover", "creating a new sport", "inventing exercise equipment",
    "cooking a dish from another culture", "learning ancestral recipes", "starting a cultural exchange",
    "creating a time capsule", "developing a family tree", "documenting oral histories", "preserving traditions",
    "starting a school newspaper", "hosting a radio show", "creating a photo essay", "filming a documentary",
    "designing adaptive equipment", "developing assistive technology", "writing in braille", "learning tactile sign language"
]

# Mario-themed constants for themed games
MARIO_CHARACTERS = [
    "Mario", "Luigi", "Princess Peach", "Princess Daisy", "Toad", "Yoshi", "Bowser", "Bowser Jr.", 
    "Wario", "Waluigi", "Donkey Kong", "Diddy Kong", "Rosalina", "Toadette", "Koopa Troopa", 
    "Goomba", "Shy Guy", "Boo", "Kamek", "Piranha Plant", "Lakitu", "Chain Chomp", "Baby Mario", 
    "Baby Luigi", "King Boo", "Dry Bones", "Nabbit", "Pauline", "Birdo"
]

MARIO_ITEMS = [
    "Super Mushroom", "Fire Flower", "Star", "Super Leaf", "Tanooki Suit", "Frog Suit", 
    "Cape Feather", "Mega Mushroom", "Mini Mushroom", "Ice Flower", "Gold Flower", "Boomerang Flower", 
    "Super Bell", "Double Cherry", "P-Switch", "POW Block", "Question Block", "Brick Block", 
    "Coin", "Red Coin", "Blue Coin", "1-Up Mushroom", "Super Star", "Yoshi Egg", "Bob-omb", 
    "Bullet Bill", "Green Shell", "Red Shell", "Blue Shell", "Banana Peel", "Mushroom Cup", 
    "Flower Cup", "Star Cup", "Special Cup", "Warp Pipe", "Flag Pole"
]

MARIO_LOCATIONS = [
    "Mushroom Kingdom", "Bowser's Castle", "Peach's Castle", "Luigi's Mansion", "Yoshi's Island", 
    "Toad Town", "Wario's Gold Mine", "Waluigi Stadium", "Rainbow Road", "Mario Circuit", 
    "Coconut Mall", "Delfino Plaza", "Bob-omb Battlefield", "Whomp's Fortress", "Cool, Cool Mountain", 
    "Jolly Roger Bay", "Big Boo's Haunt", "Dire, Dire Docks", "New Donk City", "Cascade Kingdom", 
    "Sand Kingdom", "Wooded Kingdom", "Luncheon Kingdom", "Metro Kingdom", "Seaside Kingdom", 
    "Snow Kingdom", "World 1-1", "World 1-2", "Underground Cavern", "Ghost House", "Airship", 
    "Waterworld", "Desert Land", "Sky Land", "Ice Land", "Pipe Land", "Koopa Troopa Beach", 
    "Cheep Cheep Lagoon", "Twisted Mansion"
]

MARIO_ACTIVITIES = [
    "collecting coins", "jumping on Goombas", "throwing fireballs", "riding Yoshi", "breaking blocks", 
    "finding secret areas", "rescuing Princess Peach", "racing go-karts", "battling Bowser", 
    "playing tennis", "golfing", "playing soccer", "playing baseball", "partying with friends", 
    "solving puzzles", "finding Power Stars", "collecting Shine Sprites", "using power-ups", 
    "swimming underwater", "flying with a cape", "floating with balloons", "growing giant", 
    "shrinking tiny", "throwing hammers", "climbing vines", "sliding down hills", 
    "jumping over obstacles", "finding hidden blocks", "entering warp pipes", "collecting 1-Ups", 
    "defeating bosses", "building with blocks", "exploring galaxies", "capturing enemies", 
    "finding hidden treasures", "avoiding Bullet Bills", "jumping through paintings"
] 