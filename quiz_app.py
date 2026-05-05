import random
from pathlib import Path

import streamlit as st
from PIL import Image, ImageStat


IMAGE_DIR = Path(__file__).parent
ZOOM_LEVEL = 11.0
MAX_IMAGE_WIDTH = 620
MAX_IMAGE_HEIGHT = 330
MANUAL_CROPS = {
    "torsk.png": (0.50, 0.50),
    "kuller.png": (0.50, 0.50),
    "roedspaette.png": (0.50, 0.50),
    "Pacific_Walrus_-_Bull_8247646168.jpg": (0.70, 0.50),
    "Arne.png": (0.70, 0.70),
    "No-Face.png": (0.70, 0.70),
    "ozzy.png": (0.57, 0.34),
    "sabrina.png": (0.70, 0.30),
    "solsikke.webp": (0.50, 0.10),
    "spand.png": (0.50, 0.50),
}

# True betyder "det er en torsk/torskeart".
QUIZ = [
    {"file": "torsk.png", "is_cod": True, "name": "Torsk"},
    {"file": "kuller.png", "is_cod": True, "name": "Kuller (en torskeart)"},
    {"file": "roedspaette.png", "is_cod": False, "name": "Rødspætte"},
    {"file": "Pacific_Walrus_-_Bull_8247646168.jpg", "is_cod": False, "name": "Hvalros"},
    {"file": "Arne.png", "is_cod": False, "name": "Arne"},
    {"file": "No-Face.png", "is_cod": False, "name": "No-Face / Kaonashi"},
    {"file": "ozzy.png", "is_cod": False, "name": "Ozzy Osbourne"},
    {"file": "sabrina.png", "is_cod": False, "name": "Sabrina"},
    {"file": "solsikke.webp", "is_cod": False, "name": "Solsikke"},
    {"file": "spand.png", "is_cod": False, "name": "Spand"},
]


def zoom_image(image: Image.Image, crop_position: tuple[float, float], zoom: float = ZOOM_LEVEL) -> Image.Image:
    width, height = image.size
    crop_width = max(1, int(width / zoom))
    crop_height = max(1, int(height / zoom))
    max_left = max(0, width - crop_width)
    max_top = max(0, height - crop_height)
    left = int(max_left * crop_position[0])
    top = int(max_top * crop_position[1])
    cropped = image.crop((left, top, left + crop_width, top + crop_height))
    return cropped.resize((width, height))


def fit_image(image: Image.Image, max_width: int = MAX_IMAGE_WIDTH, max_height: int = MAX_IMAGE_HEIGHT) -> Image.Image:
    image = image.copy()
    image.thumbnail((max_width, max_height))
    return image


def find_light_crop_position(image_path: Path, zoom: float = ZOOM_LEVEL) -> tuple[float, float]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    crop_width = max(1, int(width / zoom))
    crop_height = max(1, int(height / zoom))
    max_left = max(0, width - crop_width)
    max_top = max(0, height - crop_height)

    if max_left == 0 or max_top == 0:
        return (0.5, 0.5)

    candidates = []
    grid_size = 12

    for x_index in range(grid_size):
        for y_index in range(grid_size):
            left = int(max_left * x_index / (grid_size - 1))
            top = int(max_top * y_index / (grid_size - 1))
            crop = image.crop((left, top, left + crop_width, top + crop_height))
            grayscale_crop = crop.convert("L")
            stats = ImageStat.Stat(grayscale_crop)
            brightness = stats.mean[0]
            contrast = stats.stddev[0]
            too_plain_penalty = 80 if contrast < 12 else 0
            too_white_penalty = 45 if brightness > 245 else 0
            score = brightness + (contrast * 2.4) - too_plain_penalty - too_white_penalty
            candidates.append((score, left / max_left, top / max_top))

    candidates.sort(reverse=True)
    best_light_areas = candidates[:8]
    _, x_position, y_position = random.choice(best_light_areas)
    return (x_position, y_position)


def restart_quiz() -> None:
    quiz_order = QUIZ.copy()

    for _ in range(100):
        random.shuffle(quiz_order)
        fish_are_spread_out = all(
            not (quiz_order[index]["is_cod"] and quiz_order[index + 1]["is_cod"])
            for index in range(len(quiz_order) - 1)
        )
        if fish_are_spread_out:
            break

    for item in quiz_order:
        image_path = IMAGE_DIR / item["file"]
        if item["file"] in MANUAL_CROPS:
            item["crop_position"] = MANUAL_CROPS[item["file"]]
        elif image_path.exists():
            item["crop_position"] = find_light_crop_position(image_path)
        else:
            item["crop_position"] = (random.random(), random.random())

    st.session_state.quiz_order = quiz_order
    st.session_state.question = 0
    st.session_state.answers = []
    st.session_state.show_answer = False
    st.session_state.last_answer = None
    st.session_state.finished = False


st.set_page_config(page_title="Torsk eller ej?", page_icon="?", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 1rem;
        max-width: 1050px;
    }

    h1 {
        font-size: 2.1rem;
        margin-top: 0;
        margin-bottom: 0.2rem;
    }

    h3 {
        margin-top: 0.3rem;
        margin-bottom: 0.4rem;
    }

    [data-testid="stImage"] img {
        max-height: 330px;
        object-fit: contain;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "quiz_order" not in st.session_state:
    restart_quiz()

st.title("Torsk eller ej?")

question_number = st.session_state.question
quiz_order = st.session_state.quiz_order
total_questions = len(quiz_order)

if st.session_state.finished:
    score = sum(answer["correct"] for answer in st.session_state.answers)
    st.subheader(f"Du fik {score} ud af {total_questions} rigtige")

    for index, answer in enumerate(st.session_state.answers, start=1):
        correct_text = "Torsk" if answer["correct_answer"] else "Ikke torsk"
        user_text = "Torsk" if answer["user_answer"] else "Ikke torsk"
        result = "Rigtigt" if answer["correct"] else "Forkert"
        st.write(
            f"{index}. {answer['name']}: {result} - "
            f"du svarede {user_text}, facit var {correct_text}"
        )

    if st.button("Prøv igen"):
        restart_quiz()
        st.rerun()

else:
    item = quiz_order[question_number]
    image_path = IMAGE_DIR / item["file"]

    st.markdown(f"### Spørgsmål {question_number + 1} af {total_questions}")
    st.caption("Gæt om det indzoomede billede viser en torsk eller en torskeart.")
    st.progress((question_number + 1) / total_questions)

    if not image_path.exists():
        st.error(f"Mangler billede: {item['file']}")
    else:
        image = Image.open(image_path)
        left_column, right_column = st.columns([2.2, 1], gap="large")

        with left_column:
            if st.session_state.show_answer:
                st.image(fit_image(image), caption="Det oprindelige billede")
            else:
                zoomed_image = zoom_image(image, item["crop_position"])
                st.image(fit_image(zoomed_image), caption="Indzoomet billede")

        with right_column:
            if st.session_state.show_answer:
                answer = st.session_state.last_answer
                if answer["correct"]:
                    st.success("Rigtigt!")
                else:
                    st.error("Forkert!")

                correct_text = "Torsk" if answer["correct_answer"] else "Ikke torsk"
                st.write(f"Facit: **{correct_text}**")
                st.write(f"Det er: **{answer['name']}**")

                if st.button("Næste billede", type="primary"):
                    if question_number + 1 >= total_questions:
                        st.session_state.finished = True
                    else:
                        st.session_state.question += 1
                        st.session_state.show_answer = False
                        st.session_state.last_answer = None
                    st.rerun()

            else:
                st.write("Hvad gætter du på?")
                choice = st.radio(
                    "Svarmuligheder",
                    ["Torsk", "Ikke torsk"],
                    label_visibility="collapsed",
                    key=f"choice_{question_number}",
                )

                if st.button("Svar", type="primary"):
                    user_answer = choice == "Torsk"
                    correct_answer = item["is_cod"]
                    answer = {
                        "file": item["file"],
                        "name": item["name"],
                        "user_answer": user_answer,
                        "correct_answer": correct_answer,
                        "correct": user_answer == correct_answer,
                    }
                    st.session_state.answers.append(answer)
                    st.session_state.last_answer = answer
                    st.session_state.show_answer = True
                    st.rerun()
