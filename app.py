import os
import openai
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from pdf_generator import generate_pdf_roadmap
#from mu import generate_pdf_roadmap


# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI client using the API key from the environment variable
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

openai.api_key = os.environ.get("OPENAI_API_KEY")
# UI Configuration
st.set_page_config(page_title="PersonaPilot AI", page_icon="💙")


# Google Font URL and CSS Injection for Styling
font_url = "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
css_code = f"""
<style>
@import url('{font_url}');
body, .stButton > button, .stTextInput > input, .stSelectbox > select, .css-10trblm {{
    font-family: 'Roboto', sans-serif;
}}
h1, h2, h3 {{
    color: #3B6AC8; /* Unified color styling for titles and headers */
}}
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)


# ----- Helper functions (defined before UI is executed) -----
def to_score(choice: str) -> int:
    mapping = {
        'Strongly Disagree': 1,
        'Disagree': 2,
        'Neutral': 3,
        'Agree': 4,
        'Strongly Agree': 5
    }
    return mapping.get(choice, 3)


def build_personality_summary_from_choices(q1_choice: str, q2_choice: str, q3_choice: str, q4_choice: str, q5_choice: str) -> str:
    scores = {
        'analytical': to_score(q1_choice),
        'creative': to_score(q2_choice),
        'collaborative': to_score(q3_choice),
        'structured': to_score(q4_choice),
        'experimental': to_score(q5_choice)
    }
    strengths = []
    if scores['analytical'] >= 4:
        strengths.append('analytical and data-oriented')
    if scores['creative'] >= 4:
        strengths.append('creative and design-focused')
    if scores['collaborative'] >= 4:
        strengths.append('collaborative and communication-driven')
    if scores['structured'] >= 4:
        strengths.append('organized with a preference for structure and planning')
    if scores['experimental'] >= 4:
        strengths.append('curious and hands-on, comfortable with experimentation')

    growth = []
    if scores['analytical'] <= 2:
        growth.append('strengthen analytical problem-solving')
    if scores['creative'] <= 2:
        growth.append('explore more creative exercises')
    if scores['collaborative'] <= 2:
        growth.append('practice collaboration and communication')
    if scores['structured'] <= 2:
        growth.append('develop consistent routines and planning habits')
    if scores['experimental'] <= 2:
        growth.append('try lightweight experiments to learn by doing')

    parts = []
    if strengths:
        parts.append('Key strengths: ' + ', '.join(strengths) + '.')
    if growth:
        parts.append('Growth areas: ' + ', '.join(growth) + '.')
    if not parts:
        parts.append('Balanced profile with adaptable learning preferences.')
    return ' '.join(parts)


def get_career_roadmap(career, experience_level, name, personality_profile):
    prompt_message = (
        "Create a detailed, step-by-step learning roadmap for a user based on their career field, "
        "experience level, and personality profile (learning style, focus time, work preference). "
        "Include courses, books, project ideas, communities, and tools.\n\n"
        f"User name: {name}\n"
        f"Career field: {career}\n"
        f"Experience level: {experience_level}\n"
        f"Personality profile (JSON): {personality_profile}\n\n"
        "Format the output in Markdown with these sections: \n"
        "# Weekly Goals\n"
        "# Recommended Courses\n"
        "# Project Ideas\n"
        "# Communities and Forums\n"
        "# Tools and Technologies\n"
        "Use bullet points or numbered lists where appropriate."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant skilled in providing comprehensive career guidance. You offer detailed insights into various tech careers, including educational resources, practical tips, and professional development strategies"},
                {"role": "user", "content": prompt_message}
            ],
            temperature=0.5,
            max_tokens=1200,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        if response.choices:
            return response.choices[0].message.content
        else:
            return "No response was generated."
    except Exception as e:
        err_text = str(e)
        if 'insufficient_quota' in err_text or 'You exceeded your current quota' in err_text:
            return "__QUOTA_ERROR__" + err_text
        return f"Error processing your request: {err_text}"


# Display an Image Banner (replace with PersonaPilot AI banner when available)
st.image('img/banner.png', use_column_width=True)
# App Main Content
st.header('PersonaPilot AI: Personalized Roadmap')


tabs = st.tabs(['Profile', 'Roadmap'])

with tabs[0]:
    # User Inputs
    name = st.text_input('Your Name')
    career = st.text_input('Which tech career are you interested in?')
    experience_level = st.selectbox(
        'Experience level',
        ('Beginner', 'Intermediate', 'Advanced', 'Expert')
    )

    # Personality Test (required fields)
    st.subheader('Quick Personality Test')
    st.caption('We use this to tailor your roadmap to your style.')

    learning_style = st.selectbox('Learning style', ['Visual', 'Auditory', 'Kinesthetic'])
    focus_time = st.slider('Average focus time (minutes)', min_value=15, max_value=120, value=45, step=5)
    work_preference = st.selectbox('Work preference', ['Individual', 'Team'])

    preferred_resources = st.multiselect('Preferred resource types', ['Courses', 'Books', 'Videos', 'Docs/Articles', 'Interactive Labs'], default=['Courses', 'Videos'])
    planning_style = st.selectbox('Planning style', ['Flexible', 'Balanced', 'Structured'], index=1)

    persona = {
        'name': name,
        'career': career,
        'experience_level': experience_level,
        'learning_style': learning_style,
        'focus_time_minutes': focus_time,
        'work_preference': work_preference,
        'preferred_resources': preferred_resources,
        'planning_style': planning_style
    }

    if 'persona' not in st.session_state:
        st.session_state['persona'] = {}
    st.session_state['persona'] = persona

    # Additional preferences (optional)
    st.subheader('Additional preferences (optional)')
    st.caption('These help fine-tune tone and practice suggestions.')

    likert = ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']

    q1 = st.select_slider('I enjoy solving logical, data-driven problems.', options=likert, value='Agree')
    q2 = st.select_slider('I prefer creative, visual or design-focused work.', options=likert, value='Neutral')
    q3 = st.select_slider('I thrive when collaborating and communicating with others.', options=likert, value='Agree')
    q4 = st.select_slider('I like structured plans, checklists, and clear processes.', options=likert, value='Agree')
    q5 = st.select_slider('I am comfortable experimenting and learning by trying things out.', options=likert, value='Agree')

    # Build and store personality summary
    personality_summary = None
    try:
        personality_summary = build_personality_summary_from_choices(q1, q2, q3, q4, q5)
        st.session_state['personality_summary'] = personality_summary
    except Exception:
        pass

    # Generate action
    if st.button('Generate Roadmap'):
        if career and experience_level and name:
            with st.spinner(f'{name}, we are preparing your roadmap 🍳 please wait...'):
                roadmap_md = get_career_roadmap(career, experience_level, name, st.session_state.get('persona', {}))
                if isinstance(roadmap_md, str) and roadmap_md.startswith('__QUOTA_ERROR__'):
                    st.error('OpenAI quota seems exhausted. Please check your billing or try again later.')
                    st.stop()
                st.session_state['roadmap_md'] = roadmap_md
                st.session_state['personality_summary'] = personality_summary
            st.success('Ready! You can view it under the Roadmap tab below.')

def to_score(choice: str) -> int:
    mapping = {
        'Strongly Disagree': 1,
        'Disagree': 2,
        'Neutral': 3,
        'Agree': 4,
        'Strongly Agree': 5
    }
    return mapping.get(choice, 3)

def build_personality_summary() -> str:
    scores = {
        'analytical': to_score(q1),
        'creative': to_score(q2),
        'collaborative': to_score(q3),
        'structured': to_score(q4),
        'experimental': to_score(q5)
    }
    strengths = []
    if scores['analytical'] >= 4:
        strengths.append('analytical and data-oriented')
    if scores['creative'] >= 4:
        strengths.append('creative and design-focused')
    if scores['collaborative'] >= 4:
        strengths.append('collaborative and communication-driven')
    if scores['structured'] >= 4:
        strengths.append('organized with a preference for structure and planning')
    if scores['experimental'] >= 4:
        strengths.append('curious and hands-on, comfortable with experimentation')

    growth = []
    if scores['analytical'] <= 2:
        growth.append('strengthen analytical problem-solving')
    if scores['creative'] <= 2:
        growth.append('explore more creative exercises')
    if scores['collaborative'] <= 2:
        growth.append('practice collaboration and communication')
    if scores['structured'] <= 2:
        growth.append('develop consistent routines and planning habits')
    if scores['experimental'] <= 2:
        growth.append('try lightweight experiments to learn by doing')

    parts = []
    if strengths:
        parts.append('Key strengths: ' + ', '.join(strengths) + '.')
    if growth:
        parts.append('Growth areas: ' + ', '.join(growth) + '.')
    if not parts:
        parts.append('Balanced profile with adaptable learning preferences.')
    return ' '.join(parts)

# Build enforced-structure prompt
def get_career_roadmap(career, experience_level, name, personality_profile):
    prompt_message = (
        "Create a detailed, step-by-step learning roadmap for a user based on their career field, "
        "experience level, and personality profile (learning style, focus time, work preference). "
        "Include courses, books, project ideas, communities, and tools.\n\n"
        f"User name: {name}\n"
        f"Career field: {career}\n"
        f"Experience level: {experience_level}\n"
        f"Personality profile (JSON): {personality_profile}\n\n"
        "Format the output in Markdown with these sections: \n"
        "# Weekly Goals\n"
        "# Recommended Courses\n"
        "# Project Ideas\n"
        "# Communities and Forums\n"
        "# Tools and Technologies\n"
        "Use bullet points or numbered lists where appropriate."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant skilled in providing comprehensive career guidance. You offer detailed insights into various tech careers, including educational resources, practical tips, and professional development strategies"},
                {"role": "user", "content": prompt_message}
            ],
            temperature=0.5,
            max_tokens=2024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        if response.choices:
            return response.choices[0].message.content
        else:
            return "No response was generated."
    except Exception as e:
        return f"Error processing your request: {str(e)}"

# Render and PDF wiring

with tabs[1]:
    st.markdown(f"### Hello {st.session_state.get('persona', {}).get('name', '')}, here is your personalized roadmap")
    if 'roadmap_md' in st.session_state:
        with st.expander('Personality profile (used for personalization)'):
            st.json(st.session_state.get('persona', {}))
        # Indicate if demo fallback is shown
        if '(Demo)' in st.session_state['roadmap_md']:
            st.warning("Demo fallback is shown (likely due to quota or connection). Update your OPENAI_API_KEY and try again.")
        st.markdown(st.session_state['roadmap_md'], unsafe_allow_html=True)

        user_info = {
            'name': st.session_state.get('persona', {}).get('name', ''),
            'user_name': st.session_state.get('persona', {}).get('name', ''),
            'personality_summary': st.session_state.get('personality_summary', ''),
            'persona': st.session_state.get('persona', {})
        }
        pdf_filename = generate_pdf_roadmap(
            st.session_state.get('persona', {}).get('career', ''),
            st.session_state.get('persona', {}).get('experience_level', ''),
            st.session_state['roadmap_md'],
            user_info=user_info
        )
        try:
            if os.path.exists(pdf_filename):
                with open(pdf_filename, "rb") as pdf_file:
                    PDFbyte = pdf_file.read()
                st.download_button(
                    label="Download PDF Roadmap",
                    data=PDFbyte,
                    file_name=pdf_filename,
                    mime='application/pdf',
                    key="download_pdf_button"
                )
            else:
                st.error("PDF could not be generated. Please try again.")
        except Exception as e:
            st.error(f"PDF error: {e}")
    else:
        st.info("First, fill in your information on the 'Profile' tab and click 'Generate Roadmap'.")




footer = """
<style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 10px 0;
        font-family: 'Roboto', sans-serif;
        font-size: 10px;
        border-top: 1px solid #dee2e6;
        z-index: 100;
        transition: background-color 0.3s ease;
    }
    .footer:hover {
        background-color: #e9ecef;
    }
    .footer p {
        margin: 0;
        padding: 0;
    }
    .footer a {
        color: #007bff;
        text-decoration: none;
        transition: color 0.3s ease, transform 0.3s ease;
        display: inline-block;
    }
    .footer a:hover {
        color: #0056b3;
        transform: translateY(-2px);
    }
    .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 20px;
    }
    .footer-left, .footer-right {
        display: flex;
        align-items: center;
    }
    .footer-right a {
        margin-left: 20px;
    }
    .github-icon {
        width: 20px;
        height: 20px;
        margin-right: 5px;
        vertical-align: middle;
        transition: transform 0.3s ease;
    }
    .footer-right a:hover .github-icon {
        transform: rotate(360deg);
    }
</style>

<div class="footer">
    <div class="footer-content">
        <div class="footer-left">
            <p>© 2025 PersonaPilot AI</p>
        </div>
        <div class="footer-right">
            <p>Developed with <span class="heart">❤️</span> by 
                <a href="https://github.com/Elieveee/PersonaPilot/branches" target="_blank">
                    <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" class="github-icon" alt="GitHub">
                    elieveee
                </a>
            </p>
        </div>
    </div>
</div>

<script>
    const heart = document.querySelector('.heart');
    heart.addEventListener('mouseover', () => {
        heart.style.fontSize = '16px';
        heart.style.transition = 'font-size 0.3s ease';
    });
    heart.addEventListener('mouseout', () => {
        heart.style.fontSize = '10px';
    });
</script>
"""

st.markdown(footer, unsafe_allow_html=True)