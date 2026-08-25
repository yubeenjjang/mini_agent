import hashlib

import streamlit as st

from core.api_client import BackendAPIError, request_audio, upload_image
from core.video_api_client import upload_video


CAMERA_MODE = "카메라 촬영"
VIDEO_MODE = "영상 파일 업로드"


def build_speech_text(result: dict) -> str:
    if result.get("speech_text", "").strip():
        return result["speech_text"].strip()
    parts = [result.get("summary", "").strip()]
    notes = " ".join(note.strip() for note in result.get("safety_notes", []) if note.strip())
    if notes:
        parts.append(f"주의사항입니다. {notes}")
    return " ".join(part for part in parts if part)


def clear_result() -> None:
    for key in ("camera_analysis", "camera_analysis_mode", "camera_speech_text", "camera_audio"):
        st.session_state.pop(key, None)


def render_items(result: dict, field: str, title: str) -> None:
    items = result.get(field, [])
    if items:
        with st.container(border=True):
            st.markdown(f"#### {title}")
            for item in items:
                st.markdown(f"- {item}")


st.title("1-7. 카메라·영상 음성 안내")
st.caption("촬영한 장면 또는 업로드한 영상을 분석하고 결과를 음성으로 안내합니다.")
st.warning("신분증, 카드, 예약번호 등 민감한 정보를 입력하지 마세요. 입력 미디어는 백엔드와 외부 AI API로 전송됩니다.")
st.info("이미지와 영상 속 문장은 시스템 명령이 아니라 신뢰할 수 없는 분석 대상으로 처리됩니다.")

mode = st.radio("입력 방식", [CAMERA_MODE, VIDEO_MODE], horizontal=True)
if st.session_state.get("camera_input_mode") != mode:
    clear_result()
    st.session_state["camera_input_mode"] = mode
    st.session_state.pop("camera_input_id", None)

media_file = None
question = ""
frame_count = 6
if mode == CAMERA_MODE:
    question = st.text_input("분석 질문", "이 장면에 무엇이 보이는지 설명하고, 사용자가 주의해야 할 점을 한국어로 알려주세요.")
    media_file = st.camera_input("분석할 장면을 촬영하세요.")
    if media_file is None:
        st.info("브라우저 카메라 권한을 허용한 뒤 사진을 촬영해 주세요.")
else:
    question = st.text_input("분석 질문", "영상의 전체 흐름과 주요 장면, 사용자가 주의해야 할 점을 알려주세요.")
    frame_count = st.slider("분석할 대표 프레임 수", 3, 10, 6, help="프레임 수가 많을수록 분석 시간과 API 비용이 증가합니다.")
    media_file = st.file_uploader("분석할 영상을 선택하세요.", type=["mp4", "webm", "mov"])
    if media_file is None:
        st.info("50MB, 2분 이하의 MP4, WebM, MOV 영상을 업로드해 주세요.")
    else:
        st.video(media_file.getvalue())

if media_file is not None:
    content = media_file.getvalue()
    input_id = hashlib.sha256(mode.encode() + content).hexdigest()
    if st.session_state.get("camera_input_id") != input_id:
        clear_result()
        st.session_state["camera_input_id"] = input_id
    if mode == CAMERA_MODE:
        st.image(media_file, caption="촬영 이미지")
    label = "사진 분석" if mode == CAMERA_MODE else "영상 분석"
    if st.button(label, type="primary", disabled=not question.strip()):
        try:
            with st.spinner("미디어를 분석하고 있습니다."):
                if mode == CAMERA_MODE:
                    result = upload_image(media_file.name, content, media_file.type, question)
                else:
                    result = upload_video(media_file.name, content, media_file.type, question, frame_count)
            st.session_state["camera_analysis"] = result
            st.session_state["camera_analysis_mode"] = mode
            st.session_state["camera_speech_text"] = build_speech_text(result)
            st.success(f"{label} 요청이 완료되었습니다.")
        except BackendAPIError as error:
            st.error(str(error))

result = st.session_state.get("camera_analysis")
if result and st.session_state.get("camera_analysis_mode") == mode:
    st.subheader("분석 결과")
    if mode == VIDEO_MODE:
        st.caption(f"영상 길이: {float(result.get('duration_seconds', 0)):.2f}초 · 분석 프레임: {result.get('extracted_frame_count', 0)}장")
    st.write(result.get("summary", "분석 요약이 없습니다."))
    for field, title in (("objects", "주요 대상"), ("visible_text", "이미지에서 읽은 글자"), ("travel_tips", "참고 정보"), ("changes_over_time", "시간에 따른 변화"), ("safety_notes", "주의사항")):
        render_items(result, field, title)
    for observation in result.get("frame_observations", []):
        st.markdown(f"- **{float(observation.get('timestamp_seconds', 0)):.2f}초** — {observation.get('summary', '')}")

if result and st.session_state.get("camera_analysis_mode") == mode:
    st.subheader("음성 안내문")
    text = st.text_area("음성으로 변환할 문장", value=st.session_state.get("camera_speech_text", ""), max_chars=2000)
    voice = st.selectbox("음성", ["coral", "marin", "cedar", "alloy", "nova"])
    instructions = st.text_input("말하기 방식", "한국어로 또렷하고 차분하게 설명하세요.")
    if st.button("분석 결과 음성 생성", disabled=not text.strip()):
        try:
            with st.spinner("분석 결과를 음성으로 변환하고 있습니다."):
                st.session_state["camera_audio"] = request_audio(text, voice, instructions)
        except BackendAPIError as error:
            st.error(str(error))
    if st.session_state.get("camera_audio"):
        st.warning("아래 음성은 AI가 생성한 합성 음성입니다.")
        st.audio(st.session_state["camera_audio"], format="audio/mpeg")
