import streamlit as st
from model_handler import LocalLLM
from prompts import EDUCATIONAL_PROMPTS, CURRICULUM_PROMPT, PROFESSOR_PROMPTS
from curriculum import generate_curriculum_pdf
import json
from datetime import datetime
import requests  # Add this import for making HTTP requests
from youtube_transcript_api import YouTubeTranscriptApi

def main():
    # Page configuration
    st.set_page_config(
        page_title="Tutor AI",
        page_icon="📚",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 1.5rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .stButton>button {
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            background-color: #ffffff;
            color: #2c3e50;
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #f8f9fa;
            border-color: #2c3e50;
        }
        .stSelectbox select {
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }
        .stTextArea textarea {
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }
        h1, h2, h3 {
            color: #2c3e50;
            font-weight: 600;
        }
        .stMarkdown {
            color: #34495e;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        hr {
            margin: 2rem 0;
            border-color: #e0e0e0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("Tutor.ai")
    st.markdown("*Made for teachers, for the students*")

    with st.sidebar:
        st.header("Configuration")
        teaching_style = st.multiselect(
            "Teaching Styles",
            ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"]
        )
        objectives = st.text_area("Learning Objectives", 
            placeholder="Enter key learning objectives")

    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parameters")
        grade = st.selectbox("Grade", ["1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade",
             "6th Grade", "7th Grade", "8th Grade", "9th Grade", "10th Grade", "Masters/PhD"])
        
        subject = st.selectbox("Subject",
            ["Mathematics", "Science", "Language", "History", "Art", "Music", "Physical Education", "Deep Learning"])
        
        language = st.selectbox("Language",
            ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Hindi", 
             "Chinese (Simplified)", "Japanese", "Korean"])

        # Curriculum-specific inputs
        if 'duration_value' not in st.session_state:
            st.session_state.duration_value = 4
        if 'duration_unit' not in st.session_state:
            st.session_state.duration_unit = "Weeks"

    with col2:
        st.subheader("Mode")
        mode = st.radio("Select",
            ["Learn Concept", "Practice Questions", "Get Explanation", "Generate Curriculum", "Prof. Yann Lecun"])
        
        if mode == "Generate Curriculum":
            st.session_state.duration_value = st.number_input(
                "Duration Value",
                min_value=1,
                value=st.session_state.duration_value
            )
            st.session_state.duration_unit = st.selectbox(
                "Duration Unit",
                ["Weeks", "Months", "Semesters"],
                index=["Weeks", "Months", "Semesters"].index(st.session_state.duration_unit)
            )
        else:
            difficulty_level = st.select_slider(
                "Difficulty",
                options=["Basic", "Intermediate", "Advanced"],
                value="Intermediate"
            )

    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    if 'show_download'  not in st.session_state:
        st.session_state.show_download = False
    if 'pdf_bytes' not in st.session_state:
        st.session_state.pdf_bytes = None

    # Input area
    st.markdown("---")
    if mode != "Generate Curriculum":
        input_label = "❓ Your Question"
        placeholder = "Type your question here... Be as specific as possible for better results!"
    else:
        input_label = "📝 Additional Notes (Optional)"
        placeholder = "Add any specific requirements or notes for the curriculum..."

    user_input = st.text_area(
        input_label,
        value=st.session_state.user_input,
        height=100,
        placeholder=placeholder,
        max_chars=1000,
        key="input_area"
    )

    # Initialize LLM
    llm = LocalLLM()

    # def fetch_website_content(website_url):
    #     """Fetch content from the specified website."""
    #     try:
    #         response = requests.get(website_url)
    #         response.raise_for_status()  # Raise an error for bad responses
    #         return response.text  # Return the raw HTML content
    #     except requests.RequestException as e:
    #         st.error(f"Error fetching website content: {str(e)}")
    #         return None
        
    def fetch_youtube_videos(api_key, query):
        """Fetch YouTube videos based on a search query."""
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}&maxResults=5"
        response = requests.get(url)
        
        # Check if the response is successful
        if response.status_code == 200:
            try:
                return response.json().get('items', [])
                # result = []
                # for video in videos:
                #     video_id = video['id']['videoId']
                #     title = video['snippet']['title']
                #     video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                #     result.append({
                #         'title': title,
                #         'video_id': video_id,
                #         'video_url': video_url
                #     })
                # return result
            except ValueError as e:
                print(f"Error decoding JSON: {str(e)}")
                print("Response text:", response.text)  # Print the response text for debugging
                return []
        else:
            print(f"Error fetching videos: {response.status_code}")
            print("Response text:", response.text)  # Print the response text for debugging
            return []

    def fetch_video_transcript(video_id):
        """Fetch transcript of a video by its ID."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript])
        except Exception as e:
            print(f"Error fetching transcript for video {video_id}: {str(e)}")
            return None
    
    

    if st.button("📚 Generate Response", help="Click to get AI-powered teaching assistance"):
        if mode != "Generate Curriculum" and not user_input.strip():
            st.error("Please enter a question or topic first!")
            return
        
        if mode == "Prof. Yann Lecun":
            st.markdown("👨‍🏫 Prof. Yann LeCun is on his way to solve and explain your doubts and concepts...")


        # Create appropriate prompt
        if mode == "Generate Curriculum":
            prompt = CURRICULUM_PROMPT.format(
                grade=grade,
                subject=subject,
                duration_value=st.session_state.duration_value,
                duration_unit=st.session_state.duration_unit.lower(),
                language=language
            )


        if mode == "Prof. Yann Lecun":
            
            # api_key = 'AIzaSyDwC4L7KV83avQVAshiAHeJGHfJUZuy9wM'
            # videos = fetch_youtube_videos(api_key, "Yann Lecun")
            # transcripts = []

            # print(transcripts)

            # for video in videos:
            #     video_id = video['id']['videoId']
            #     transcript = fetch_video_transcript(video_id)
            #     if transcript:
            #         transcripts.append(transcript)

            # combined_transcripts = "\n".join(transcripts)
            
            # website_url = "https://atcold.github.io/NYU-DLSP21/"
            # print("Website fetced succesully")  # Replace with the actual website URL
            # website_content = fetch_website_content(website_url)
            # if website_content:
                # Process the website_content to extract relevant information

            api_key = 'AIzaSyDwC4L7KV83avQVAshiAHeJGHfJUZuy9wM'  # Replace with your YouTube Data API key
            query = "Yann LeCun's brief explanation on {user_input}"
            
            # Fetch videos
            videos = fetch_youtube_videos(api_key, query)
            
            # Initialize a variable to hold all transcripts
            combined_transcripts = ""

            for video in videos:
                if 'id' in video and 'videoId' in video['id']:  # Check if 'videoId' exists
                    video_id = video['id']['videoId']
                    transcript = fetch_video_transcript(video_id)
                    if transcript:
                        combined_transcripts += f"Transcript for '{video['snippet']['title']}':\n{transcript}\n\n"
                        print(combined_transcripts)
                else:
                    print(f"Skipping item without videoId: {video}")
            # Print the combined transcripts

        
            prompt = f"Hey, I want you to take on the persona of Professor Yann LeCun and strictly explain things from:\n{combined_transcripts}\n\n just like he would in a lecture. Start by greeting the students as Prof. Yann LeCun, introduce the topic concisely, and then explain it with real-world examples and practical applications. Keep the explanations brief but insightful, ensuring clarity without excessive complexity. Throughout the explanation, adopt LeCuns engaging and accessible teaching style. End by inviting students to ask questions if they have any doubts. The topic for today's explanation is:{user_input}"
        # else:
            
        else:
            prompt = EDUCATIONAL_PROMPTS[mode].format(
                grade=grade,
                subject=subject,
                topic=user_input,
                language=language
            )

        # Generate response
        response_placeholder = st.empty()
        full_response = ""
        st.session_state.show_download = False

        with st.spinner("🤖 Thinking..."):
            try:
                response_stream = llm.generate(
                    prompt=prompt,
                    teaching_style=teaching_style if teaching_style else None
                )

                for chunk in response_stream:
                    if chunk:
                        try:
                            chunk_data = json.loads(chunk.decode('utf-8').strip('data: ').strip())
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                content = chunk_data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    full_response += content
                                    response_placeholder.markdown(full_response + "▌")
                        except json.JSONDecodeError:
                            continue

                response_placeholder.markdown(full_response)
                st.session_state.conversation_history.append((user_input, full_response))
                st.session_state.user_input = ""
                
                # Generate PDF for curriculum
                if mode == "Generate Curriculum":
                    duration = f"{st.session_state.duration_value} {st.session_state.duration_unit}"
                    pdf_bytes = generate_curriculum_pdf(
                        full_response,
                        grade=grade,
                        subject=subject,
                        duration=duration
                    )
                    st.session_state.show_download = True
                    
                    st.download_button(
                        label="📥 Download Curriculum PDF",
                        data=pdf_bytes,
                        file_name=f"{grade.replace(' ', '_')}_{subject}_Curriculum.pdf",
                        mime="application/pdf"
                    )

                st.rerun()

            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

    # Download button   
    if st.session_state.show_download and st.session_state.pdf_bytes is not None:
        st.markdown("---")
        st.success("🎉 Curriculum generated successfully! Click the button below to download the PDF.")
        st.download_button(
        label="📥 Download Curriculum PDF",
        data=st.session_state.pdf_bytes,
        file_name=f"{subject.replace(' ', '_')}_{grade.replace(' ', '_')}_Curriculum.pdf",
        mime="application/pdf",
        key="download_curriculum",
        help="Click to download the formatted PDF curriculum",
        type="primary"
    )


    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("### History")
        
        for i, (question, answer) in enumerate(reversed(st.session_state.conversation_history)):
            msg_num = len(st.session_state.conversation_history) - i
            
            st.markdown(f"**Q{msg_num}:**")
            st.markdown(f"```\n{question}\n```" if question else "No specific question")
            
            st.markdown(f"**A{msg_num}:**")
            st.markdown(answer)
            
            cols = st.columns([0.1, 0.1, 0.1, 0.7])
            with cols[0]:
                st.button(f"💾_{msg_num}")
            with cols[1]:
                st.button(f"👍_{msg_num}")
            with cols[2]:
                st.button(f"👎_{msg_num}")
            
            st.markdown("---")

if __name__ == "__main__":
    main()