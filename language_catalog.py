"""Editorial song-language pools used for mood-aware Spotify discovery.

Spotify Search does not return a track language. Each entry here has been
selected for its original vocal language; Spotify resolution checks title and
artist before a track is shown. The groups describe musical energy, not a
claim about the listener's feelings.
"""

LANGUAGES = ("Any", "English", "Hindi", "Tamil", "Telugu", "Malayalam", "Kannada", "Punjabi")

# Each tuple is (track title, credited singer/artist, short explanation, genres).
SONGS = {
    "Hindi": {
        "bright": [
            ("Badtameez Dil", "Benny Dayal", "Playful dance energy", ("Pop", "Dance")),
            ("Gallan Goodiyaan", "Yashita Sharma", "Joyful group chorus", ("Pop", "Dance")),
            ("Kala Chashma", "Amar Arshi", "A bold party rhythm", ("Pop", "Dance")),
            ("Ghungroo", "Arijit Singh", "Light dance momentum", ("Pop", "Dance")),
        ],
        "calm": [
            ("Iktara", "Kavita Seth", "Soft, unhurried warmth", ("Acoustic", "Pop")),
            ("Kabira", "Arijit Singh", "A grounded singalong", ("Acoustic", "Pop")),
            ("Raabta", "Arijit Singh", "Gentle romantic flow", ("Pop",)),
            ("Ilahi", "Arijit Singh", "Open, easygoing optimism", ("Pop",)),
        ],
        "reflective": [
            ("Agar Tum Saath Ho", "Alka Yagnik", "Room for reflection", ("Acoustic", "Pop")),
            ("Channa Mereya", "Arijit Singh", "Cathartic ballad", ("Acoustic", "Pop")),
            ("Tum Hi Ho", "Arijit Singh", "Deeply emotional melody", ("Acoustic", "Pop")),
            ("Phir Le Aya Dil", "Arijit Singh", "Quiet melancholy", ("Acoustic",)),
        ],
        "intense": [
            ("Zinda", "Siddharth Mahadevan", "Driving determination", ("Rock", "Pop")),
            ("Sultan", "Sukhwinder Singh", "Strong forward momentum", ("Pop",)),
            ("Apna Time Aayega", "Ranveer Singh", "Focused, defiant energy", ("Hip-Hop",)),
            ("Kar Har Maidaan Fateh", "Sukhwinder Singh", "A powerful release", ("Pop",)),
        ],
    },
    "Tamil": {
        "bright": [
            ("Arabic Kuthu", "Anirudh Ravichander", "Bright dance pulse", ("Dance", "Pop")),
            ("Rowdy Baby", "Dhanush", "Playful bounce", ("Dance", "Pop")),
            ("Vaathi Coming", "Anirudh Ravichander", "Celebratory drive", ("Dance",)),
            ("Aaluma Doluma", "Anirudh Ravichander", "Big festival energy", ("Dance",)),
        ],
        "calm": [
            ("Munbe Vaa", "Shreya Ghoshal", "Soft romantic melody", ("Acoustic", "Pop")),
            ("Nenjukkul Peidhidum", "Hariharan", "Easy, flowing warmth", ("Acoustic", "Pop")),
            ("Maruvaarthai", "Sid Sriram", "Slow reflective warmth", ("Acoustic",)),
            ("Vaseegara", "Bombay Jayashri", "Gentle, familiar comfort", ("Acoustic",)),
        ],
        "reflective": [
            ("Kanave Kanave", "Anirudh Ravichander", "Intimate melancholy", ("Acoustic", "Pop")),
            ("Po Nee Po", "Mohit Chauhan", "A tender emotional release", ("Acoustic",)),
            ("Thenmozhi", "Santhosh Narayanan", "Quiet longing", ("Acoustic", "Pop")),
            ("Ennai Vittu", "Yuvan Shankar Raja", "A reflective ballad", ("Pop",)),
        ],
        "intense": [
            ("Hukum", "Anirudh Ravichander", "Commanding rock energy", ("Rock", "Dance")),
            ("Badass", "Anirudh Ravichander", "A hard, driving beat", ("Rock", "Dance")),
            ("Pathala Pathala", "Anirudh Ravichander", "Rhythmic release", ("Dance",)),
            ("Naa Ready", "Anirudh Ravichander", "Fast festival momentum", ("Dance",)),
        ],
    },
    "Telugu": {
        "bright": [
            ("Butta Bomma", "Armaan Malik", "Light, playful pop", ("Pop", "Dance")),
            ("Naatu Naatu", "Rahul Sipligunj", "Explosive dance energy", ("Dance",)),
            ("Seeti Maar", "Jaspreet Jasz", "Party momentum", ("Dance",)),
            ("Ringa Ringa", "Priya Hemesh", "Festive rhythm", ("Dance",)),
        ],
        "calm": [
            ("Samajavaragamana", "Sid Sriram", "Smooth melodic warmth", ("Acoustic", "Pop")),
            ("Inkem Inkem Inkem Kaavaale", "Sid Sriram", "Soft romantic flow", ("Acoustic", "Pop")),
            ("Vachindamma", "Sid Sriram", "Gentle lift", ("Pop",)),
            ("Oh Sita Hey Rama", "S. P. B. Charan", "Tender, unhurried duet", ("Acoustic",)),
        ],
        "reflective": [
            ("Adiga Adiga", "Sid Sriram", "Intimate longing", ("Acoustic",)),
            ("Nee Kannu Neeli Samudram", "Javed Ali", "Emotional ballad", ("Acoustic", "Pop")),
            ("Oke Oka Lokam", "Sid Sriram", "Quiet romance", ("Acoustic",)),
            ("Priyathama Priyathama", "Chinmayi", "A reflective melody", ("Acoustic",)),
        ],
        "intense": [
            ("Pushpa Pushpa", "Nakash Aziz", "Defiant forward drive", ("Dance", "Pop")),
            ("Saami Saami", "Mounika Yadav", "High-energy folk pulse", ("Dance",)),
            ("Oo Antava Oo Oo Antava", "Indravathi Chauhan", "A sharp dance groove", ("Dance",)),
            ("Jai Balayya", "Karimullah", "Forceful celebration", ("Dance",)),
        ],
    },
    "Malayalam": {
        "bright": [
            ("Entammede Jimikki Kammal", "Vineeth Sreenivasan", "Festive singalong", ("Dance", "Pop")),
            ("Illuminati", "Dabzee", "Playful dance energy", ("Dance", "Hip-Hop")),
            ("Pala Palli", "Athul Narukara", "Big folk celebration", ("Dance",)),
            ("Kudukku", "Vineeth Sreenivasan", "Bouncy, easy joy", ("Dance", "Pop")),
        ],
        "calm": [
            ("Malare", "Vijay Yesudas", "Tender romantic melody", ("Acoustic", "Pop")),
            ("Darshana", "Hesham Abdul Wahab", "Warm, breezy flow", ("Acoustic", "Pop")),
            ("Pavizha Mazha", "K. S. Harisankar", "Soft and spacious", ("Acoustic",)),
            ("Aaradhike", "Sooraj Santhosh", "Gentle reassurance", ("Acoustic", "Pop")),
        ],
        "reflective": [
            ("Uyiril Thodum", "Sooraj Santhosh", "Quiet longing", ("Acoustic",)),
            ("Parayuvaan", "Sid Sriram", "Tender contemplation", ("Acoustic", "Pop")),
            ("Manikya Malaraya Poovi", "Vineeth Sreenivasan", "Soft nostalgic warmth", ("Acoustic",)),
            ("Nee Himamazhayayi", "K. S. Harisankar", "A reflective melody", ("Acoustic",)),
        ],
        "intense": [
            ("Kalapakkaara", "Shreya Ghoshal", "Punchy dance release", ("Dance",)),
            ("Thallumaala Paattu", "Hrithik Jayakish", "Fast, restless rhythm", ("Hip-Hop", "Dance")),
            ("Jada", "Sushin Shyam", "Hard driving energy", ("Rock", "Dance")),
            ("Kotha Raja", "Jakes Bejoy", "A powerful beat", ("Dance",)),
        ],
    },
    "Kannada": {
        "bright": [
            ("Ra Ra Rakkamma", "Nakash Aziz", "Playful dance pulse", ("Dance",)),
            ("Belageddu", "Vijay Prakash", "Easy, sunny momentum", ("Pop",)),
            ("3 Peg", "Chandan Shetty", "Party groove", ("Hip-Hop", "Dance")),
            ("Party Freakz", "Chandan Shetty", "Upbeat release", ("Dance", "Hip-Hop")),
        ],
        "calm": [
            ("Singara Siriye", "Vijay Prakash", "Grounded, flowing warmth", ("Acoustic", "Pop")),
            ("Anisuthide", "Sonu Nigam", "Soft romantic feeling", ("Acoustic", "Pop")),
            ("Ninnindale", "Sonu Nigam", "Gentle melodic lift", ("Acoustic", "Pop")),
            ("Minchagi Neenu Baralu", "Sonu Nigam", "Warm and unhurried", ("Acoustic",)),
        ],
        "reflective": [
            ("Ondu Malebillu", "Armaan Malik", "Tender introspection", ("Acoustic", "Pop")),
            ("Marali Manasaagide", "Sanjith Hegde", "Quiet longing", ("Acoustic",)),
            ("Soul of Dia", "Sanjith Hegde", "A soft emotional pause", ("Acoustic",)),
            ("Baanali Badalago", "Sonu Nigam", "Reflective melody", ("Acoustic",)),
        ],
        "intense": [
            ("Tagaru Banthu Tagaru", "Anthony Daasan", "Raw folk drive", ("Dance",)),
            ("Salaam Rocky Bhai", "Vijay Prakash", "Bold cinematic force", ("Rock",)),
            ("Dheera Dheera", "Srinivas", "Heroic energy", ("Rock",)),
            ("Toofan", "Brijesh Shandilya", "A forceful rush", ("Rock",)),
        ],
    },
    "Punjabi": {
        "bright": [
            ("Brown Munde", "AP Dhillon", "Easy swagger", ("Hip-Hop", "Pop")),
            ("Lover", "Diljit Dosanjh", "Bright romantic pop", ("Pop", "Dance")),
            ("3 Peg", "Sharry Mann", "Celebratory dance pulse", ("Dance",)),
            ("Born To Shine", "Diljit Dosanjh", "Confident forward motion", ("Pop", "Dance")),
        ],
        "calm": [
            ("Khaab", "Akhil", "Gentle melodic warmth", ("Acoustic", "Pop")),
            ("Qismat", "Ammy Virk", "A tender slow burn", ("Acoustic", "Pop")),
            ("Sakhiyaan", "Maninder Buttar", "Easy romantic rhythm", ("Pop",)),
            ("Soch", "Harrdy Sandhu", "Quiet, familiar comfort", ("Acoustic",)),
        ],
        "reflective": [
            ("Mann Bharrya", "B Praak", "Cathartic heartache", ("Acoustic", "Pop")),
            ("Filhall", "B Praak", "An emotional ballad", ("Acoustic", "Pop")),
            ("Kina Chir", "The PropheC", "Hushed longing", ("Pop",)),
            ("Excuses", "AP Dhillon", "Cool melancholy", ("Hip-Hop", "Pop")),
        ],
        "intense": [
            ("G.O.A.T.", "Diljit Dosanjh", "Confident beat", ("Hip-Hop", "Pop")),
            ("We Rollin", "Shubh", "Focused, assertive groove", ("Hip-Hop",)),
            ("52 Bars", "Karan Aujla", "Sharp lyrical drive", ("Hip-Hop",)),
            ("Old Skool", "Sidhu Moose Wala", "Hard-edged momentum", ("Hip-Hop",)),
        ],
    },
}


MOOD_GROUPS = {
    "happy": {"Match": ("bright", "intense"), "Improve": ("calm", "bright")},
    "sad": {"Match": ("reflective", "calm"), "Improve": ("calm", "bright")},
    "angry": {"Match": ("intense", "bright"), "Improve": ("calm", "reflective")},
    "fear": {"Match": ("reflective", "calm"), "Improve": ("calm", "bright")},
    "disgust": {"Match": ("intense", "reflective"), "Improve": ("calm", "bright")},
    "surprise": {"Match": ("bright", "intense"), "Improve": ("calm", "bright")},
    "neutral": {"Match": ("calm", "reflective"), "Improve": ("bright", "calm")},
}
