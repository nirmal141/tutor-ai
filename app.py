import streamlit as st
from model_handler import LocalLLM
from prompts import EDUCATIONAL_PROMPTS, TEACHING_STYLES, CURRICULUM_PROMPT
import onnxruntime as ort
from curriculum import generate_curriculum_pdf
import io
import json

def check_npu_availability():
    return False  # Simplified for deployment

def main():
    # Page configuration
    st.set_page_config(
        page_title="Tutor AI`",
        page_icon="📚",
        layout="wide"
    )

    # Updated Custom CSS for a more sophisticated look
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

    # Simplified header
    st.title("Tutor.ai")
    st.markdown("*Made for teachers, for the students*")

    # Device status indicator
    device = "CPU"  # Always use CPU for now
    
    with st.sidebar:
        st.header("Configuration")
        teaching_style = st.multiselect(
            "Teaching Styles",
            ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"]
        )
        
        st.markdown("---")
        
        
        objectives = st.text_area("Learning Objectives", 
            placeholder="Enter key learning objectives")

    # Main content area with cleaner layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parameters")
        grade = st.selectbox("Grade", ["1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade",
             "6th Grade", "7th Grade", "8th Grade", "9th Grade", "10th Grade"])
        
        subject = st.selectbox("Subject",
            ["Mathematics", "Science", "Language", "History", "Art", "Music", "Physical Education"])
        
        language = st.selectbox("Language",
            ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Hindi", 
             "Chinese (Simplified)", "Japanese", "Korean"])

    with col2:
        st.subheader("Mode")
        mode = st.radio("Select",
            ["Learn Concept", "Practice Questions", "Get Explanation"])
        
        difficulty_level = st.select_slider("Difficulty",
            options=["Basic", "Intermediate", "Advanced"],
            value="Intermediate")

    # Initialize session state for conversation history if it doesn't exist
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Question input area
    st.markdown("---")
    st.subheader("❓ Your Question")
    
    # Initialize the input key in session state if it doesn't exist
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
        
    
    user_input = st.text_area(
        "Enter your question or topic:",
        value=st.session_state.user_input,
        height=100,
        placeholder="Type your question here... Be as specific as possible for better results!",
        max_chars=1000,
        key="input_area"
    )
    
    # Initialize LLM and generate response
    llm = LocalLLM(device=device)
    
    if st.button("📚 Generate Response", help="Click to get AI-powered teaching assistance"):
        if not user_input.strip():
            st.error("Please enter a question or topic first!")
            return
        
        # Create the prompt based on selected mode
        prompt = EDUCATIONAL_PROMPTS[mode].format(
            grade=grade,
            subject=subject,
            topic=user_input,
            language=language
        )
        
        # Create a placeholder for the streaming response
        response_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("🤖 Thinking..."):
            try:
                # Get the streaming response
                response_stream = llm.generate(
                    prompt=prompt,
                    
                    teaching_style=teaching_style if teaching_style else None
                )
                
                # Process the stream
                for chunk in response_stream:
                    if chunk:
                        try:
                            # Parse the chunk
                            chunk_data = json.loads(chunk.decode('utf-8').strip('data: ').strip())
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                content = chunk_data['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    full_response += content
                                    # Update the response in real-time
                                    response_placeholder.markdown(full_response + "▌")
                        except json.JSONDecodeError:
                            continue
                
                # Final update without the cursor
                response_placeholder.markdown(full_response)
                
                # Add to conversation history
                st.session_state.conversation_history.append((user_input, full_response))
                
                # Clear the input
                st.session_state.user_input = ""
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
    
    # Updated conversation history display
    if st.session_state.conversation_history:
        st.markdown("### History")
        
        for i, (question, answer) in enumerate(reversed(st.session_state.conversation_history)):
            msg_num = len(st.session_state.conversation_history) - i
            
            st.markdown(f"**Q{msg_num}:**")
            st.markdown(f"```\n{question}\n```")
            
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
    
    # Curriculum Generator Tab
    if st.sidebar.checkbox("📚 Show Curriculum Generator"):
        st.markdown("## 📚 Curriculum Generator")
        
        col1, col2 = st.columns(2)
        with col1:
            duration_value = st.number_input("Duration", min_value=1, max_value=12, value=1)
        with col2:
            duration_unit = st.selectbox(
                "Duration Unit",
                ["Weeks", "Months"]
            )
        
        curriculum_prompt = CURRICULUM_PROMPT.format(
            grade=grade,
            subject=subject,
            duration_value=duration_value,
            duration_unit=duration_unit,
            language=language
        )
        
        if st.button("🎯 Generate Curriculum"):
            with st.spinner("Generating curriculum plan..."):
                try:
                    # Create a placeholder for the streaming response
                    response_placeholder = st.empty()
                    curriculum_content = ""
                    
                    # Get the streaming response
                    response_stream = llm.generate(
                        prompt=curriculum_prompt,
                        max_length=4096,
                        
                    )
                    
                    # Process the stream
                    for chunk in response_stream:
                        if chunk:
                            try:
                                # Parse the chunk
                                chunk_data = json.loads(chunk.decode('utf-8').strip('data: ').strip())
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    content = chunk_data['choices'][0].get('delta', {}).get('content', '')
                                    if content:
                                        curriculum_content += content
                                        # Update the response in real-time
                                        response_placeholder.markdown(curriculum_content + "▌")
                            except json.JSONDecodeError:
                                continue
                    
                    # Final update without the cursor
                    response_placeholder.markdown(curriculum_content)
                    
                    # Generate PDF
                    try:
                        pdf = generate_curriculum_pdf(
                            curriculum_content,  # Now passing the complete string
                            grade,
                            subject,
                            f"{duration_value} {duration_unit}"
                        )
                        
                        # Create download button
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf,
                            file_name=f"curriculum_{grade}_{subject}_{duration_value}_{duration_unit}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        
                except Exception as e:
                    st.error(f"Error generating curriculum: {str(e)}")

if __name__ == "__main__":
    main()
