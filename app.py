import streamlit as st
from model_handler import LocalLLM
from prompts import EDUCATIONAL_PROMPTS, TEACHING_STYLES, CURRICULUM_PROMPT
from pdf_extractor import extract_text_from_pdf
import onnxruntime as ort
from curriculum import generate_curriculum_pdf
import io
import json

def check_npu_availability():
    providers = ort.get_available_providers()
    return 'NPUExecutionProvider' in providers

def main():
    # Page configuration
    st.set_page_config(
        page_title="AI Educational Assistant",
        page_icon="📚",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
        }
        .stSelectbox {
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header section with title and description
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📚 AI Educational Assistant")
        st.markdown("*Your personal AI tutor powered by advanced NPU acceleration*")
    
    # Device status indicator
    use_npu = check_npu_availability()
    device = "NPU" if use_npu else "CPU"
    
    with st.sidebar:
        st.header("💻‍🏫 Teacher Tools")
        teaching_style = st.multiselect(
            "Select Teaching Styles:",
            ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"],
            help="Select multiple teaching styles to incorporate"
        )
        
        st.header("📚 Curriculum Resources")
        uploaded_file = st.file_uploader("Upload curriculum/lesson plan (PDF)", type="pdf")
        additional_context = ""
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                additional_context = extract_text_from_pdf(uploaded_file)
            st.success("Document processed successfully!")
            
        st.header("🎯 Learning Objectives")
        objectives = st.text_area("Set learning objectives:", 
            placeholder="Enter the key learning objectives for this lesson")
    
    # Main content area
    st.markdown("---")
    
    # Two-column layout for input parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="css-1r6slb0">
                <h3>🎯 Learning Parameters</h3>
        """, unsafe_allow_html=True)
        
        grade = st.selectbox(
            "Grade Level:",
            ["1st Grade", "2nd Grade", "3rd Grade", "4th Grade", "5th Grade",
             "6th Grade", "7th Grade", "8th Grade", "9th Grade", "10th Grade"]
        )
        
        subject = st.selectbox(
            "Subject:",
            ["Mathematics", "Science", "Language", "History", "Art", "Music", "Physical Education"]
        )
        
        language = st.selectbox(
            "Output Language:",
            ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Hindi", 
             "Chinese (Simplified)", "Japanese", "Korean"]
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.subheader("🔄 Teaching Mode")
        mode = st.radio(
            "Select Mode:",
            ["Learn Concept", "Practice Questions", "Get Explanation"],
            help="Choose the type of teaching resource you need"
        )
        
        difficulty_level = st.select_slider(
            "Content Difficulty:",
            options=["Basic", "Intermediate", "Advanced"],
            value="Intermediate",
            help="Adjust difficulty level of the content"
        )
    
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
                    additional_context=additional_context,
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
                st.experimental_rerun()
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
    
    # Display conversation history
    st.markdown("### 📝 Conversation History:")
    
    # Reverse the conversation history to show latest first
    for i, (question, answer) in enumerate(reversed(st.session_state.conversation_history)):
        # Calculate the actual message number (counting from the end)
        msg_num = len(st.session_state.conversation_history) - i
        
        # Question
        st.markdown(f"**Question {msg_num}:**")
        st.markdown(f"```\n{question}\n```")
        
        # Answer
        st.markdown(f"**Response {msg_num}:**")
        st.markdown(answer)
        
        # Feedback buttons for each response
        col1, col2, col3, col4 = st.columns([1,1,1,3])
        with col1:
            st.button(f"💾 Save_{msg_num}")
        with col2:
            st.button(f"👍 Helpful_{msg_num}")
        with col3:
            st.button(f"👎 Not Helpful_{msg_num}")
        
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
                        additional_context=additional_context
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
