import streamlit as st
from openai import OpenAI
from typing import List, Dict
import json

#Test Commit

# Configure Streamlit page settings and initialize OpenAI client
st.set_page_config(page_title="Architect Guru", page_icon="🏗️", layout="wide")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

class ArchitectAgent:
    """
    Main agent class that handles interactions with the OpenAI API
    and generates architecture recommendations
    """
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        
    def _get_completion(self, messages: List[Dict]) -> str:
        """
        Helper method to make API calls to OpenAI
        Args:
            messages: List of message dictionaries for the chat completion
        Returns:
            The content of the model's response
        """
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def generate_questions(self, project_description: str, challenges: List[str]) -> List[str]:
        """
        Generates relevant questions about the project based on initial description
        Args:
            project_description: Initial project description
            challenges: List of selected challenges
        Returns:
            List of questions to gather more project information
        """
        prompt = f"""
        As an expert software architect, generate relevant questions to gather more information about this project.
        
        Project Description: {project_description}
        Main Challenges: {', '.join(challenges)}
        
        Generate 5-8 specific questions about:
        1. The industry and business context
        2. Technical requirements and constraints
        3. Team capabilities and resources
        4. Timeline and budget considerations
        5. Security and compliance needs (if applicable)
        
        IMPORTANT: Return ONLY a JSON array of strings, with each string being a question.
        Format example: ["Question 1?", "Question 2?", "Question 3?"]
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Always respond with valid JSON arrays when asked."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback in case of invalid JSON
            st.error("Error parsing response. Using fallback questions.")
            return [
                "What industry is this project targeting?",
                "What are your technical requirements and constraints?",
                "What is your team size and technical expertise?",
                "What is your timeline and budget?",
                "What are your security and compliance requirements?"
            ]
    
    def generate_architecture_plan(self, project_info: Dict, answers: Dict) -> Dict:
        """
        Generates a comprehensive architecture plan based on all gathered information
        Args:
            project_info: Dictionary containing project description and challenges
            answers: Dictionary containing answers to the generated questions
        Returns:
            Dictionary containing three sections of the architecture plan
        """
        # First, analyze the information
        analysis_prompt = f"""
        Analyze this software project information:
        
        Project Description: {project_info['description']}
        Challenges: {', '.join(project_info['challenges'])}
        
        Additional Information:
        {json.dumps(answers, indent=2)}
        
        Provide a detailed analysis of the requirements and constraints.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Always respond with valid JSON when requested."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        analysis = self._get_completion(messages)
        
        # Generate the architecture plan
        plan_prompt = f"""
        Based on this analysis:
        
        {analysis}
        
        Generate a comprehensive architecture plan with three different versions.
        
        IMPORTANT: Return your response as a JSON object with exactly this structure:
        {{
            "technical": "markdown content here",
            "management": "markdown content here",
            "executive": "markdown content here"
        }}
        
        Include in each section:
        1. Technical Overview: Detailed technical architecture including patterns, technologies, and implementation guidelines
        2. Management Summary: Focus on resources, timeline, risks, and key decisions
        3. Executive Brief: High-level overview focusing on business value, costs, and advantages
        """
        
        messages.append({"role": "assistant", "content": analysis})
        messages.append({"role": "user", "content": plan_prompt})
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback in case of invalid JSON
            st.error("Error parsing architecture plan. Using fallback response.")
            return {
                "technical": "# Technical Overview\n\nUnable to generate technical overview. Please try again.",
                "management": "# Management Summary\n\nUnable to generate management summary. Please try again.",
                "executive": "# Executive Brief\n\nUnable to generate executive brief. Please try again."
            }

def initialize_session_state():
    """
    Initializes all required session state variables for the Streamlit app
    This ensures persistence of data between reruns and handles the multi-step form process
    """
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0  # Controls the current step in the workflow
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {}  # Stores basic project information
    if 'questions' not in st.session_state:
        st.session_state.questions = []  # Stores generated questions
    if 'answers' not in st.session_state:
        st.session_state.answers = {}  # Stores user's answers to questions
    if 'architecture_plan' not in st.session_state:
        st.session_state.architecture_plan = None  # Stores the final architecture plan
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}  # Stores form input values for persistence

def main():
    """
    Main application function that handles the UI and workflow
    Implements a three-step process:
    1. Project Description Input
    2. Detailed Questions
    3. Architecture Plan Display
    """
    st.title("🏗️ Architect Guru")
    st.subheader("Your AI Software Architecture Consultant")
    
    # Initialize components
    agent = ArchitectAgent()
    initialize_session_state()
    
    # Step 1: Project Description Input
    if st.session_state.current_step == 0:
        st.write("### Project Description")
        with st.form("project_form"):
            # Form inputs for project details
            project_name = st.text_input("Project Name", 
                                       value=st.session_state.form_data.get('project_name', ''))
            project_description = st.text_area("Project Description",
                                             value=st.session_state.form_data.get('project_description', ''))
            challenges = st.multiselect(
                "Select your main challenges:",
                ["Security", "Time to Market", "Performance", "User Experience", "Scalability", "Cost Efficiency"]
            )
            submit_button = st.form_submit_button("Generate Questions")
            
            # Handle form submission
            if submit_button and project_description:
                # Store form data for persistence
                st.session_state.form_data = {
                    'project_name': project_name,
                    'project_description': project_description
                }
                st.session_state.project_info = {
                    "description": project_description,
                    "challenges": challenges
                }
                # Generate questions based on input
                with st.spinner("Generating questions..."):
                    st.session_state.questions = agent.generate_questions(
                        project_description, challenges
                    )
                st.session_state.current_step = 1
                st.rerun()
    
    # Step 2: Detailed Questions
    elif st.session_state.current_step == 1:
        st.write("### Project Analysis Questions")
        with st.form("questions_form"):
            # Display generated questions and collect answers
            answers = {}
            for i, question in enumerate(st.session_state.questions):
                answer = st.text_input(
                    f"Q{i+1}: {question}",
                    key=f"q_{i}",
                    help="Type 'don't know' if you're unsure about this aspect"
                )
                if answer:
                    answers[question] = answer
            
            submit_answers = st.form_submit_button("Generate Architecture Plan")
            
            # Handle answers submission
            if submit_answers:
                st.session_state.answers = answers
                with st.spinner("Analyzing and generating architecture plan..."):
                    st.session_state.architecture_plan = agent.generate_architecture_plan(
                        st.session_state.project_info,
                        st.session_state.answers
                    )
                st.session_state.current_step = 2
                st.rerun()
    
    # Step 3: Architecture Plan Display
    elif st.session_state.current_step == 2:
        st.write("### Architecture Recommendation")
        
        # Display the architecture plan in tabs
        tab1, tab2, tab3 = st.tabs(["Technical Overview", "Management Summary", "Executive Brief"])
        
        with tab1:
            st.markdown(st.session_state.architecture_plan['technical'])
        with tab2:
            st.markdown(st.session_state.architecture_plan['management'])
        with tab3:
            st.markdown(st.session_state.architecture_plan['executive'])
        
        # Reset button
        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main() 