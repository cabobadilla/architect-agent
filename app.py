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
        Generates specific, quantitative questions about the project
        Args:
            project_description: Initial project description
            challenges: List of selected challenges
        Returns:
            List of precise, measurable questions
        """
        prompt = f"""
        As an expert software architect, generate specific, quantitative questions to gather detailed information about this project.
        
        Project Description: {project_description}
        Main Challenges: {', '.join(challenges)}
        
        Generate 8-10 precise questions that will help determine concrete technical and organizational requirements. Focus on:

        1. Business Context & Metrics:
           - Expected user base and growth projections
           - Specific performance/availability requirements
           - Compliance and regulatory requirements

        2. Technical Constraints & Scale:
           - Current/expected transaction volumes
           - Data storage and processing requirements
           - Integration requirements with specific systems

        3. Team & Organization:
           - Current team size and expertise levels
           - Development practices and tools in use
           - Organizational constraints and preferences

        4. Implementation Context:
           - Specific timeline milestones
           - Budget constraints and ROI expectations
           - Deployment and operational requirements

        IMPORTANT: 
        - Make questions specific and quantifiable where possible
        - Ask for concrete numbers, percentages, or specific requirements
        - Focus on measurable aspects that will impact architectural decisions
        
        Return ONLY a JSON array of strings, with each string being a question.
        Format example: ["What is the expected peak number of concurrent users in the first year?", "What is your target response time for critical transactions in milliseconds?"]
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Generate specific, measurable questions and always respond with valid JSON arrays."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            st.error("Error parsing response. Using fallback questions.")
            return [
                "What is your expected user base size and growth rate for the first year?",
                "What are your specific performance requirements (response times, throughput)?",
                "What is your expected data volume and growth rate?",
                "What specific regulatory requirements must be met?",
                "What is your current team size and technical expertise distribution?",
                "What is your specific timeline and major milestones?",
                "What is your budget range for implementation and maintenance?",
                "What are your specific availability and reliability requirements?"
            ]
    
    def generate_architecture_plan(self, project_info: Dict, answers: Dict) -> Dict:
        """
        Generates two architectural options with technical, process, and people dimensions
        Args:
            project_info: Dictionary containing project description and challenges
            answers: Dictionary containing answers to the generated questions
        Returns:
            Dictionary containing the architecture plan options
        """
        analysis_prompt = f"""
        Analyze this software project information:
        
        Project Description: {project_info['description']}
        Challenges: {', '.join(project_info['challenges'])}
        
        Additional Information:
        {json.dumps(answers, indent=2)}
        
        Provide a detailed analysis focusing on technical requirements, process needs, and organizational impacts.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Always respond with valid JSON when requested."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        analysis = self._get_completion(messages)
        
        plan_prompt = f"""
        Based on this analysis:
        
        {analysis}
        
        Generate TWO distinct architectural options. For each option, provide detailed recommendations across three dimensions:

        1. Technical Architecture:
           - Core technologies and patterns
           - System components and their interactions
           - Key technical decisions and their rationale
           - Expected benefits and potential trade-offs

        2. Key Processes:
           - Development and deployment processes
           - Operational procedures
           - Quality assurance approaches
           - Change management recommendations

        3. People & Organization:
           - Team structure recommendations
           - Required skills and training needs
           - Collaboration patterns
           - Organizational changes needed

        IMPORTANT: Return your response as a JSON object with exactly this structure:
        {{
            "option1": {{
                "technical": "markdown content with technical architecture details",
                "process": "markdown content with key process recommendations",
                "people": "markdown content with organizational recommendations",
                "rationale": "markdown content explaining the reasoning and benefits"
            }},
            "option2": {{
                "technical": "markdown content with technical architecture details",
                "process": "markdown content with key process recommendations",
                "people": "markdown content with organizational recommendations",
                "rationale": "markdown content explaining the reasoning and benefits"
            }}
        }}

        For each recommendation:
        - Clearly explain the rationale behind each decision
        - Highlight specific benefits and potential trade-offs
        - Include quantitative impacts where possible
        - Reference industry best practices or successful case studies
        """
        
        messages.append({"role": "assistant", "content": analysis})
        messages.append({"role": "user", "content": plan_prompt})
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            st.error("Error parsing architecture plan. Using fallback response.")
            return {
                "option1": {
                    "technical": "# Technical Architecture\n\nUnable to generate technical details. Please try again.",
                    "process": "# Key Processes\n\nUnable to generate process recommendations. Please try again.",
                    "people": "# People & Organization\n\nUnable to generate organizational recommendations. Please try again.",
                    "rationale": "# Rationale & Benefits\n\nUnable to generate rationale. Please try again."
                },
                "option2": {
                    "technical": "# Technical Architecture\n\nUnable to generate technical details. Please try again.",
                    "process": "# Key Processes\n\nUnable to generate process recommendations. Please try again.",
                    "people": "# People & Organization\n\nUnable to generate organizational recommendations. Please try again.",
                    "rationale": "# Rationale & Benefits\n\nUnable to generate rationale. Please try again."
                }
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
        st.write("### Architecture Recommendations")
        
        option_tab1, option_tab2 = st.tabs(["Option 1", "Option 2"])
        
        with option_tab1:
            tech_tab1, proc_tab1, people_tab1, rationale_tab1 = st.tabs([
                "Technical Architecture", "Key Processes", 
                "People & Organization", "Rationale & Benefits"
            ])
            with tech_tab1:
                st.markdown(st.session_state.architecture_plan['option1']['technical'])
            with proc_tab1:
                st.markdown(st.session_state.architecture_plan['option1']['process'])
            with people_tab1:
                st.markdown(st.session_state.architecture_plan['option1']['people'])
            with rationale_tab1:
                st.markdown(st.session_state.architecture_plan['option1']['rationale'])
        
        with option_tab2:
            tech_tab2, proc_tab2, people_tab2, rationale_tab2 = st.tabs([
                "Technical Architecture", "Key Processes", 
                "People & Organization", "Rationale & Benefits"
            ])
            with tech_tab2:
                st.markdown(st.session_state.architecture_plan['option2']['technical'])
            with proc_tab2:
                st.markdown(st.session_state.architecture_plan['option2']['process'])
            with people_tab2:
                st.markdown(st.session_state.architecture_plan['option2']['people'])
            with rationale_tab2:
                st.markdown(st.session_state.architecture_plan['option2']['rationale'])
        
        # Reset button
        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main() 