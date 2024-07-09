import streamlit as st
from streamlit_cropper import st_cropper
import streamlit_cropper
from PIL import Image

st.set_page_config(layout="wide")

from encoder import load_model
from milvus_utils import get_db


def _recommended_box2(img: Image, aspect_ratio: tuple = None) -> dict:
    width, height = img.size
    return {
        "left": int(0),
        "top": int(0),
        "width": int(width - 2),
        "height": int(height - 2),
    }


streamlit_cropper._recommended_box = _recommended_box2

extractor = load_model("resnet34")
client = get_db()

# Logo
st.sidebar.image("./pics/Milvus_Logo_Official.png", width=200)

# Title
st.title("Image Similarity Search :frame_with_picture: ")

query_image = "temp.jpg"
cols = st.columns(5)

uploaded_file = st.sidebar.file_uploader("Choose an image...", type="jpeg")

if uploaded_file is not None:
    with open("temp.jpg", "wb") as f:
        f.write(uploaded_file.getbuffer())
    # cropper
    # Get a cropped image from the frontend
    uploaded_img = Image.open(uploaded_file)
    width, height = uploaded_img.size

    new_width = 370
    new_height = int((new_width / width) * height)
    uploaded_img = uploaded_img.resize((new_width, new_height))

    st.sidebar.text(
        "Query Image",
        help="Edit the bounding box to change the ROI (Region of Interest).",
    )
    with st.sidebar.empty():
        cropped_img = st_cropper(
            uploaded_img,
            box_color="#4fc4f9",
            realtime_update=True,
            aspect_ratio=(16, 9),
        )

    show_distance = st.sidebar.toggle("Show Distance")

    # top k value slider
    value = st.sidebar.slider("Select top k results shown", 10, 100, 20, step=1)

    @st.cache_resource
    def get_image_embedding(image_path):
        return extractor(image_path)

    image_embedding = get_image_embedding(cropped_img)

    results = client.search(
        "image_embeddings",
        data=[extractor(cropped_img)],
        limit=value,
        output_fields=["filename"],
        search_params={"metric_type": "COSINE"},
    )
    search_results = results[0]

    for i, info in enumerate(search_results):
        img_info = info["entity"]
        imgName = img_info["filename"]
        score = info["distance"]
        img = Image.open(imgName)
        cols[i % 5].image(img, use_column_width=True)
        if show_distance:
            cols[i % 5].write(f"Score: {score:.3f}")
