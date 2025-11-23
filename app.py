import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="SAT 단어 학습",
    page_icon="📚",
    layout="wide"
)

# 세션 상태 초기화
if 'word_index' not in st.session_state:
    st.session_state.word_index = 0
if 'study_mode' not in st.session_state:
    st.session_state.study_mode = 'flashcard'
if 'known_words' not in st.session_state:
    st.session_state.known_words = set()
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_score' not in st.session_state:
    st.session_state.quiz_score = 0

# 단어 데이터 로드
@st.cache_data
def load_words():
    try:
        df = pd.read_csv('sat_words.csv')
        return df
    except FileNotFoundError:
        st.error("단어 데이터 파일을 찾을 수 없습니다. sat_words.csv 파일이 필요합니다.")
        return pd.DataFrame()

df = load_words()

if df.empty:
    st.stop()

# 사이드바
with st.sidebar:
    st.title("📚 SAT 단어 학습")
    st.markdown("---")
    
    mode = st.radio(
        "학습 모드 선택",
        ["플래시카드", "퀴즈", "단어 목록", "검색"],
        key="mode_selector"
    )
    
    st.markdown("---")
    st.metric("전체 단어 수", len(df))
    st.metric("알고 있는 단어", len(st.session_state.known_words))
    st.metric("학습률", f"{len(st.session_state.known_words) / len(df) * 100:.1f}%")
    
    if st.button("초기화"):
        st.session_state.known_words = set()
        st.session_state.word_index = 0
        st.session_state.quiz_answers = {}
        st.session_state.quiz_score = 0
        st.rerun()

# 메인 콘텐츠
if mode == "플래시카드":
    st.header("🎴 플래시카드 모드")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 단어 선택
        word_options = st.selectbox(
            "단어 선택",
            options=range(len(df)),
            format_func=lambda x: f"{x+1}. {df.iloc[x]['word']}",
            key="word_selector"
        )
        st.session_state.word_index = word_options
        
        st.markdown("---")
        
        # 플래시카드
        card_style = """
        <style>
        .flashcard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin: 20px 0;
            min-height: 300px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .word {
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .meaning {
            font-size: 24px;
            margin-top: 20px;
        }
        .example {
            font-size: 18px;
            margin-top: 30px;
            font-style: italic;
            opacity: 0.9;
        }
        </style>
        """
        st.markdown(card_style, unsafe_allow_html=True)
        
        current_word = df.iloc[st.session_state.word_index]
        show_meaning = st.checkbox("뜻 보기", key="show_meaning")
        
        card_html = f"""
        <div class="flashcard">
            <div class="word">{current_word['word']}</div>
            <div class="meaning">{current_word['pronunciation'] if 'pronunciation' in current_word else ''}</div>
        """
        
        if show_meaning:
            card_html += f"""
            <div class="meaning">{current_word['meaning']}</div>
            <div class="example">{current_word['example'] if 'example' in current_word and pd.notna(current_word['example']) else ''}</div>
            """
        
        card_html += "</div>"
        st.markdown(card_html, unsafe_allow_html=True)
        
        # 네비게이션 버튼
        col_prev, col_next, col_random = st.columns(3)
        
        with col_prev:
            if st.button("◀ 이전", use_container_width=True):
                st.session_state.word_index = (st.session_state.word_index - 1) % len(df)
                st.rerun()
        
        with col_next:
            if st.button("다음 ▶", use_container_width=True):
                st.session_state.word_index = (st.session_state.word_index + 1) % len(df)
                st.rerun()
        
        with col_random:
            if st.button("🎲 랜덤", use_container_width=True):
                st.session_state.word_index = random.randint(0, len(df) - 1)
                st.rerun()
        
        st.markdown("---")
        
        # 학습 상태 표시
        word_id = current_word['word']
        is_known = word_id in st.session_state.known_words
        
        if is_known:
            st.success(f"✅ '{current_word['word']}' 단어를 알고 있습니다.")
            if st.button("❌ 모르는 단어로 표시", use_container_width=True):
                st.session_state.known_words.discard(word_id)
                st.rerun()
        else:
            st.info(f"💡 '{current_word['word']}' 단어를 학습 중입니다.")
            if st.button("✅ 아는 단어로 표시", use_container_width=True):
                st.session_state.known_words.add(word_id)
                st.rerun()

elif mode == "퀴즈":
    st.header("📝 퀴즈 모드")
    
    quiz_size = st.slider("퀴즈 문제 수", 5, min(50, len(df)), 10)
    
    if st.button("새 퀴즈 시작"):
        st.session_state.quiz_words = random.sample(range(len(df)), min(quiz_size, len(df)))
        st.session_state.quiz_answers = {}
        st.session_state.quiz_score = 0
        st.session_state.current_quiz = 0
        st.rerun()
    
    if 'quiz_words' in st.session_state:
        current_quiz_idx = st.session_state.get('current_quiz', 0)
        
        if current_quiz_idx < len(st.session_state.quiz_words):
            word_idx = st.session_state.quiz_words[current_quiz_idx]
            current_word = df.iloc[word_idx]
            
            st.subheader(f"문제 {current_quiz_idx + 1} / {len(st.session_state.quiz_words)}")
            st.markdown(f"### {current_word['word']}")
            
            # 정답과 오답 선택
            correct_answer = current_word['meaning']
            wrong_answers = df[df['word'] != current_word['word']].sample(min(3, len(df)-1))['meaning'].tolist()
            all_answers = [correct_answer] + wrong_answers
            random.shuffle(all_answers)
            
            selected_answer = st.radio(
                "뜻을 선택하세요:",
                all_answers,
                key=f"quiz_{current_quiz_idx}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("답안 제출", use_container_width=True):
                    if selected_answer == correct_answer:
                        st.success("✅ 정답입니다!")
                        st.session_state.quiz_score += 1
                    else:
                        st.error(f"❌ 오답입니다. 정답: {correct_answer}")
                    st.session_state.quiz_answers[current_quiz_idx] = selected_answer == correct_answer
                    st.session_state.current_quiz = current_quiz_idx + 1
                    st.rerun()
            
            with col2:
                if st.button("정답 보기", use_container_width=True):
                    st.info(f"정답: {correct_answer}")
                    if 'example' in current_word and pd.notna(current_word['example']):
                        st.write(f"예문: {current_word['example']}")
        else:
            # 퀴즈 완료
            st.success("🎉 퀴즈 완료!")
            score = st.session_state.quiz_score
            total = len(st.session_state.quiz_words)
            percentage = (score / total) * 100
            
            st.metric("점수", f"{score} / {total} ({percentage:.1f}%)")
            
            # 결과 차트
            results_df = pd.DataFrame({
                '결과': ['정답', '오답'],
                '개수': [score, total - score]
            })
            st.bar_chart(results_df.set_index('결과'))
            
            if st.button("새 퀴즈 시작"):
                st.session_state.quiz_words = random.sample(range(len(df)), min(quiz_size, len(df)))
                st.session_state.quiz_answers = {}
                st.session_state.quiz_score = 0
                st.session_state.current_quiz = 0
                st.rerun()

elif mode == "단어 목록":
    st.header("📋 단어 목록")
    
    # 필터 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        filter_option = st.selectbox(
            "필터",
            ["전체", "알고 있는 단어", "모르는 단어"]
        )
    
    with col2:
        search_term = st.text_input("검색", placeholder="단어나 뜻으로 검색...")
    
    # 데이터 필터링
    display_df = df.copy()
    
    if filter_option == "알고 있는 단어":
        display_df = display_df[display_df['word'].isin(st.session_state.known_words)]
    elif filter_option == "모르는 단어":
        display_df = display_df[~display_df['word'].isin(st.session_state.known_words)]
    
    if search_term:
        mask = (
            display_df['word'].str.contains(search_term, case=False, na=False) |
            display_df['meaning'].str.contains(search_term, case=False, na=False)
        )
        display_df = display_df[mask]
    
    st.write(f"**{len(display_df)}개 단어**")
    
    # 테이블 표시
    if len(display_df) > 0:
        # 상태 표시 컬럼 추가
        display_df['상태'] = display_df['word'].apply(
            lambda x: '✅' if x in st.session_state.known_words else '💡'
        )
        
        # 컬럼 순서 조정
        cols = ['상태', 'word', 'meaning']
        if 'pronunciation' in display_df.columns:
            cols.insert(2, 'pronunciation')
        if 'example' in display_df.columns:
            cols.append('example')
        
        display_df = display_df[[c for c in cols if c in display_df.columns]]
        display_df.columns = ['상태', '단어', '발음', '뜻', '예문'] if 'pronunciation' in display_df.columns else ['상태', '단어', '뜻', '예문']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("검색 결과가 없습니다.")

elif mode == "검색":
    st.header("🔍 단어 검색")
    
    search_query = st.text_input("단어나 뜻으로 검색", placeholder="검색어를 입력하세요...")
    
    if search_query:
        results = df[
            df['word'].str.contains(search_query, case=False, na=False) |
            df['meaning'].str.contains(search_query, case=False, na=False)
        ]
        
        if len(results) > 0:
            st.write(f"**{len(results)}개 결과**")
            
            for idx, row in results.iterrows():
                with st.expander(f"**{row['word']}** - {row['meaning']}"):
                    if 'pronunciation' in row and pd.notna(row['pronunciation']):
                        st.write(f"**발음:** {row['pronunciation']}")
                    if 'example' in row and pd.notna(row['example']):
                        st.write(f"**예문:** {row['example']}")
                    
                    word_id = row['word']
                    is_known = word_id in st.session_state.known_words
                    
                    if is_known:
                        st.success("✅ 알고 있는 단어")
                        if st.button(f"❌ 모르는 단어로 표시", key=f"unknown_{idx}"):
                            st.session_state.known_words.discard(word_id)
                            st.rerun()
                    else:
                        st.info("💡 학습 중인 단어")
                        if st.button(f"✅ 아는 단어로 표시", key=f"known_{idx}"):
                            st.session_state.known_words.add(word_id)
                            st.rerun()
        else:
            st.warning("검색 결과가 없습니다.")
    else:
        st.info("검색어를 입력하세요.")

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>SAT 단어 학습 앱 | Made with Streamlit</div>",
    unsafe_allow_html=True
)

