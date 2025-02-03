import streamlit as st
from model_handler import LocalLLM
from prompts import EDUCATIONAL_PROMPTS, CURRICULUM_PROMPT, PROFESSOR_PROMPTS
from curriculum import generate_curriculum_pdf
import json
from datetime import datetime
import requests  # Add this import for making HTTP requests
from youtube_transcript_api import YouTubeTranscriptApi
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

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
            ["Learn Concept", "Practice Questions", "Get Explanation", "Generate Curriculum", "Prof. Yann Lecun", "Andrew Ng"])
        
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
    def get_embeddings(text_chunks):
        """Generate embeddings for each chunk of text."""
        return embedding_model.encode(text_chunks, convert_to_numpy=True)
    
    def store_transcripts_in_faiss(transcripts):
        """Store transcript embeddings in a FAISS index."""
        
        # Split transcripts into chunks (sentences or paragraphs)
        text_chunks = transcripts.split("\n")  
        
        # Convert text chunks to embeddings
        embeddings = get_embeddings(text_chunks)
        
        # Create FAISS index
        dimension = embeddings.shape[1]  # Get embedding size
        index = faiss.IndexFlatL2(dimension)  
        index.add(embeddings)  # Add embeddings to the index
        
        return index, text_chunks  # Return index and original text chunks
    
    def retrieve_relevant_transcript(index, text_chunks, query, top_k=3, chunk_size=150):
        """Retrieve the most relevant transcript segments based on the query."""
        
        # Get embedding for query
        query_embedding = get_embeddings([query])
        
        # Search in FAISS index
        distances, indices = index.search(query_embedding, top_k)
        
        # Retrieve top-k most relevant text segments
        relevant_texts = []
        for idx in indices[0]:
            start_idx = max(0, idx - chunk_size // 2)  # Ensure valid index
            end_idx = min(len(text_chunks), idx + chunk_size // 2)
            relevant_texts.append(" ".join(text_chunks[start_idx:end_idx]))

        return " ".join(relevant_texts)
        
    def fetch_youtube_videos(api_key, query):
        """Fetch YouTube videos based on a search query."""
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}&maxResults=2&order=date"
        response = requests.get(url)
        
        # Check if the response is successful
        if response.status_code == 200:
            try:
                return response.json().get('items', [])
            except ValueError as e:
                print(f"Error decoding JSON: {str(e)}")
                print("Response text:", response.text)  # Print the response text for debugging
                return []
        else:
            print(f"Error fetching videos: {response.status_code}")
            print("Response text:", response.text)  # Print the response text for debugging
            return []

    def fetch_video_transcript(video_id):
        """Fetch transcript of a video and store as embeddings."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([entry['text'] for entry in transcript])
            
            # Store transcript in FAISS
            index, text_chunks = store_transcripts_in_faiss(full_text)
            
            return index, text_chunks  # Return the index and stored text
        except Exception as e:
            print(f"Error fetching transcript: {str(e)}")
            return None, None

        
    embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # Lightweight & fast



    
    

    if st.button("📚 Generate Response", help="Click to get AI-powered teaching assistance"):
        if mode != "Generate Curriculum" and not user_input.strip():
            st.error("Please enter a question or topic first!")
            return
        
        if mode == "Prof. Yann Lecun":
            st.markdown("👨‍🏫 Prof. Yann LeCun is on his way to solve and explain your doubts and concepts...")

        if mode == "Andrew Ng":
            st.markdown("👨‍🏫 Prof. Andrew Ng is on his way to solve and explain your doubts and concepts...")


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

            api_key = 'AIzaSyDwC4L7KV83avQVAshiAHeJGHfJUZuy9wM'  # Replace with your YouTube Data API key
            query = f"{user_input} by Prof Yann LeCun"

            
            # Fetch videos
            videos = fetch_youtube_videos(api_key, query)
            
            # Initialize a variable to hold all transcripts

            for video in videos:
                if 'id' in video and 'videoId' in video['id']:  # Check if 'videoId' exists
                    video_id = video['id']['videoId']
                    index, text_chunks = fetch_video_transcript(video_id)
                    if index and text_chunks:
                        relevant_text = retrieve_relevant_transcript(index, text_chunks, user_input, top_k=5)
                        print(relevant_text)
                        
                else:
                    print(f"Skipping item without videoId: {video}")
            # Print the combined transcripts

        
                prompt = f"Hey, I want you to take on the persona of Prof. Yann LeCun and explain:\n\n{relevant_text}\n\n using his teaching style."
        # else:

        elif mode == "Andrew Ng":

            api_key = 'AIzaSyDwC4L7KV83avQVAshiAHeJGHfJUZuy9wM'  # Replace with your YouTube Data API key
            query = f"{user_input} by Andrew Ng"

            
            # Fetch videos
            videos = fetch_youtube_videos(api_key, query)
            
            for video in videos:
                if 'id' in video and 'videoId' in video['id']:  # Check if 'videoId' exists
                    video_id = video['id']['videoId']
                    index, text_chunks = fetch_video_transcript(video_id)
                    if index and text_chunks:
                        relevant_text = retrieve_relevant_transcript(index, text_chunks, user_input, top_k=5)
                        
                else:
                    print(f"Skipping item without videoId: {video}")
            # Print the combined transcripts

        
                prompt = f"Hey, I want you to take on the persona of Andrew Ng and explain:\n\n{relevant_text}\n\n using his teaching style."
       
            
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