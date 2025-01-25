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
    
    def generate_questions(self, project_description: str, main_challenge: str, challenges: List[str]) -> List[str]:
        """
        Generates a mix of quantitative and qualitative questions
        """
        prompt = f"""
        As an expert software architect, generate a balanced mix of quantitative and qualitative questions to gather comprehensive information about this project.
        
        Project Description: {project_description}
        Main Challenge: {main_challenge}
        Additional Challenges: {', '.join(challenges)}
        
        Generate 10-12 questions that combine specific metrics with strategic insights. Focus on:

        1. Problem Understanding & Context:
           - Core problem definition and impact
           - Business goals and success criteria
           - Current pain points and limitations

        2. Technical & Operational Requirements:
           - Scale and performance needs (with specific metrics)
           - Integration points and dependencies
           - Operational constraints and requirements

        3. Team & Organizational Context:
           - Team capabilities and structure
           - Stakeholder expectations
           - Cultural and process considerations

        4. Implementation & Delivery:
           - Timeline and resource constraints
           - Risk factors and mitigation strategies
           - Quality and compliance requirements

        IMPORTANT: 
        - Balance specific metrics with strategic insights
        - Include both quantitative measures and qualitative aspects
        - Focus on both immediate needs and long-term implications
        - Ensure questions help understand the main challenge deeply
        
        Return ONLY a JSON array of strings, with each string being a question.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Generate a balanced mix of strategic and specific questions."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            st.error("Error parsing response. Using fallback questions.")
            return [
                "What specific problem or pain point is driving this project?",
                "What are your key success criteria for this solution?",
                "What is your expected user base size and growth rate?",
                "What specific technical constraints must be considered?",
                "How does this project align with your business strategy?",
                "What are your specific performance requirements?",
                "What is your team's current experience with similar projects?",
                "What are the most critical risks you foresee?",
                "What integration points are required with existing systems?",
                "What is your preferred approach to delivering this solution?"
            ]
    
    def generate_architecture_plan(self, project_info: Dict, answers: Dict) -> Dict:
        """
        Generates architecture options with clear rationale and perspectives
        """
        analysis_prompt = f"""
        Analyze this software project information:
        
        Project Description: {project_info['description']}
        Main Challenge: {project_info['main_challenge']}
        Additional Challenges: {', '.join(project_info['challenges'])}
        
        Detailed Responses:
        {json.dumps(answers, indent=2)}
        
        Provide a detailed analysis focusing on how the solution addresses the main challenge while considering all requirements.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect. Always respond with valid JSON when requested."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        analysis = self._get_completion(messages)
        
        plan_prompt = f"""
        Based on this analysis:
        
        {analysis}
        
        Generate TWO distinct architectural options that specifically address the main challenge while considering all requirements.
        
        For each option, provide a comprehensive view across these perspectives:

        1. Technical Architecture (in the 'technical' field):
           - How the solution addresses the main challenge
           - Core technologies and patterns with justification
           - System components and their interactions
           - Scalability and performance considerations

        2. Key Processes (in the 'process' field):
           - Development and delivery approach
           - Operational procedures and monitoring
           - Risk management and quality assurance
           - Change and release management

        3. People & Organization (in the 'people' field):
           - Team structure and responsibilities
           - Required skills and learning curve
           - Collaboration and communication patterns
           - Cultural and organizational impact

        4. Rationale (in the 'rationale' field):
           - Direct mapping to the main challenge
           - Key advantages and differentiators
           - Trade-offs and their justification
           - Implementation strategy and timeline
           - Cost implications and ROI considerations

        IMPORTANT:
        - Clearly explain how each option addresses the main challenge
        - Provide concrete examples and specific recommendations
        - Include both immediate and long-term considerations
        - Highlight key decision points and their implications

        Format all content using markdown with clear sections and bullet points.
        """
        
        messages.append({"role": "assistant", "content": analysis})
        messages.append({"role": "user", "content": plan_prompt})
        
        try:
            response = self._get_completion(messages)
            plan = json.loads(response)
            
            # Validate the response structure
            if not all(key in plan for key in ['option1', 'option2']):
                raise KeyError("Missing required options in response")
            
            for option in ['option1', 'option2']:
                if not all(key in plan[option] for key in ['technical', 'process', 'people', 'rationale']):
                    raise KeyError(f"Missing required fields in {option}")
            
            return plan
            
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"Error parsing architecture plan: {str(e)}. Using fallback response.")
            return {
                "option1": {
                    "technical": "# Technical Architecture\n\n- Unable to generate technical details. Please try again.",
                    "process": "# Key Processes\n\n- Unable to generate process recommendations. Please try again.",
                    "people": "# People & Organization\n\n- Unable to generate organizational recommendations. Please try again.",
                    "rationale": "# Rationale & Benefits\n\n- Unable to generate rationale. Please try again."
                },
                "option2": {
                    "technical": "# Technical Architecture\n\n- Unable to generate technical details. Please try again.",
                    "process": "# Key Processes\n\n- Unable to generate process recommendations. Please try again.",
                    "people": "# People & Organization\n\n- Unable to generate organizational recommendations. Please try again.",
                    "rationale": "# Rationale & Benefits\n\n- Unable to generate rationale. Please try again."
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
    """
    st.title("🏗️ Architect Guru")
    st.subheader("Your AI Software Architecture Consultant")
    
    # Initialize components
    agent = ArchitectAgent()
    initialize_session_state()
    
    # Add a reset button in the sidebar that's always visible
    with st.sidebar:
        st.write("### Navigation")
        if st.button("🏠 Reset / Start Over", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        # Show current step
        st.write("Current Step:", 
                ["Project Description", "Analysis Questions", "Architecture Plan"][st.session_state.current_step])
    
    # Step 1: Project Description Input
    if st.session_state.current_step == 0:
        st.write("### Project Description")
        with st.form("project_form"):
            project_name = st.text_input("Project Name", 
                                       value=st.session_state.form_data.get('project_name', ''))
            
            # Add main challenge input
            main_challenge = st.text_area(
                "What is the main challenge or problem you're trying to solve?",
                value=st.session_state.form_data.get('main_challenge', ''),
                help="Describe the core problem or challenge that motivated this project"
            )
            
            project_description = st.text_area(
                "Project Description",
                value=st.session_state.form_data.get('project_description', ''),
                help="Provide a detailed description of your project"
            )
            
            additional_challenges = st.multiselect(
                "Select additional challenges:",
                ["Security", "Time to Market", "Performance", "User Experience", "Scalability", "Cost Efficiency"]
            )
            
            submit_button = st.form_submit_button("Generate Questions")
            
            if submit_button and project_description and main_challenge:
                st.session_state.form_data = {
                    'project_name': project_name,
                    'main_challenge': main_challenge,
                    'project_description': project_description
                }
                st.session_state.project_info = {
                    "description": project_description,
                    "main_challenge": main_challenge,
                    "challenges": additional_challenges
                }
                with st.spinner("Generating questions..."):
                    st.session_state.questions = agent.generate_questions(
                        project_description, main_challenge, additional_challenges
                    )
                st.session_state.current_step = 1
                st.rerun()

    # Step 2: Detailed Questions
    elif st.session_state.current_step == 1:
        # Add a back button
        if st.button("← Back to Project Description"):
            st.session_state.current_step = 0
            st.rerun()
            
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
        # Add a back button
        if st.button("← Back to Questions"):
            st.session_state.current_step = 1
            st.rerun()
            
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

if __name__ == "__main__":
    main() 