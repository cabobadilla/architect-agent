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
    
    def generate_scope_questions(self, project_description: str, main_challenge: str, challenges: List[str]) -> List[str]:
        """
        First phase: Generate questions to clarify scope and constraints
        """
        prompt = f"""
        As an expert software architect, analyze this initial project information and generate questions to clarify the scope and constraints.
        
        Project Description: {project_description}
        Main Challenge: {main_challenge}
        Additional Challenges: {', '.join(challenges)}
        
        Generate 6-8 essential questions focusing on:

        1. Business Context & Scope:
           - Business objectives and success metrics
           - Project boundaries and limitations
           - Key stakeholders and their expectations
           - Timeline and budget constraints

        2. Technical Boundaries:
           - Current system limitations
           - Integration requirements
           - Non-functional requirements
           - Technical constraints

        IMPORTANT: 
        - Questions should help define clear project boundaries
        - Focus on understanding limitations and constraints
        - Aim to uncover potential roadblocks early
        - Keep questions focused and specific
        
        Return ONLY a JSON array of strings, with each string being a question.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect focusing on scope definition."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            return self._get_fallback_scope_questions()

    def generate_solution_questions(self, project_info: Dict, scope_answers: Dict) -> List[str]:
        """
        Second phase: Generate questions to explore potential solutions
        """
        prompt = f"""
        Based on the scope information provided:
        
        Project Info: {json.dumps(project_info, indent=2)}
        Scope Answers: {json.dumps(scope_answers, indent=2)}
        
        Generate 6-8 questions to explore potential solution approaches. Focus on:

        1. Technical Solution Space:
           - Architectural patterns that might fit
           - Technology stack preferences
           - Scalability and performance needs
           - Security requirements

        2. Implementation Approach:
           - Development methodology
           - Team capabilities and needs
           - Risk mitigation strategies
           - Quality assurance requirements

        IMPORTANT:
        - Questions should help identify the best solution approaches
        - Focus on both technical and organizational aspects
        - Consider the constraints identified in the scope phase
        
        Return ONLY a JSON array of strings, with each string being a question.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect focusing on solution exploration."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._get_completion(messages)
            return json.loads(response)
        except json.JSONDecodeError:
            return self._get_fallback_solution_questions()

    def generate_final_recommendations(self, project_info: Dict, scope_answers: Dict, solution_answers: Dict) -> Dict:
        """
        Final phase: Generate detailed solution recommendations
        """
        analysis_prompt = f"""
        As an expert software architect, analyze all gathered information to generate optimal solution recommendations:
        
        Project Description: {project_info['description']}
        Main Challenge: {project_info['main_challenge']}
        Additional Challenges: {', '.join(project_info.get('challenges', []))}
        
        Scope Information:
        {json.dumps(scope_answers, indent=2)}
        
        Solution Details:
        {json.dumps(solution_answers, indent=2)}
        
        Provide a comprehensive analysis focusing on key requirements, constraints, and potential approaches.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect creating detailed solution recommendations. Always provide comprehensive, well-structured responses using markdown formatting."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        analysis = self._get_completion(messages)
        
        recommendation_prompt = f"""
        Based on the analysis:
        
        {analysis}
        
        Generate TWO distinct architectural options that best address the requirements and constraints.
        
        VERY IMPORTANT: Format your response as a JSON object with this EXACT structure:
        {{
            "option1": {{
                "overview": "# Solution Overview\\n\\n## Key Points\\n- Point 1\\n- Point 2\\n\\n## Main Benefits\\n1. Benefit 1\\n2. Benefit 2",
                "technical": "# Technical Details\\n\\n## Architecture\\n- Component 1\\n- Component 2\\n\\n## Technology Stack\\n1. Tech 1\\n2. Tech 2",
                "implementation": "# Implementation Strategy\\n\\n## Phases\\n1. Phase 1\\n2. Phase 2\\n\\n## Team Structure\\n- Team 1\\n- Team 2",
                "rationale": "# Decision Rationale\\n\\n## Why This Solution\\n- Reason 1\\n- Reason 2\\n\\n## Risk Analysis\\n1. Risk 1\\n2. Risk 2"
            }},
            "option2": {{
                "overview": "...",
                "technical": "...",
                "implementation": "...",
                "rationale": "..."
            }}
        }}

        For each option, include:

        1. Solution Overview (overview):
           - High-level architecture description
           - Key architectural decisions
           - How it addresses the main challenge
           - Primary benefits and trade-offs

        2. Technical Details (technical):
           - Detailed technology stack
           - Component architecture
           - Integration patterns
           - Security and scalability measures

        3. Implementation Strategy (implementation):
           - Phased approach
           - Team structure and roles
           - Risk mitigation steps
           - Timeline and milestones

        4. Decision Rationale (rationale):
           - Why this solution is recommended
           - Cost-benefit analysis
           - Risk assessment
           - Critical success factors

        IMPORTANT:
        - Use proper markdown formatting with headers, lists, and sections
        - Be specific and detailed in each section
        - Explain the reasoning behind each decision
        - Include concrete examples and metrics where possible
        - Ensure the response is a valid JSON object
        """
        
        messages.append({"role": "assistant", "content": analysis})
        messages.append({"role": "user", "content": recommendation_prompt})
        
        try:
            response = self._get_completion(messages)
            recommendations = json.loads(response)
            
            # Validate the response structure
            required_sections = ['overview', 'technical', 'implementation', 'rationale']
            for option in ['option1', 'option2']:
                if option not in recommendations:
                    raise KeyError(f"Missing {option} in recommendations")
                for section in required_sections:
                    if section not in recommendations[option]:
                        raise KeyError(f"Missing {section} in {option}")
                    if not recommendations[option][section].strip():
                        raise ValueError(f"Empty content in {option}.{section}")
            
            return recommendations
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            st.error(f"Error generating recommendations: {str(e)}")
            return {
                "option1": {
                    "overview": """# Solution Overview

## Architecture Approach
- Modular, scalable architecture
- Focus on maintainability and extensibility

## Key Benefits
1. Scalable solution
2. Easy to maintain
3. Cost-effective implementation

## Main Features
- Core functionality implementation
- Integration capabilities
- Security measures""",
                    "technical": """# Technical Details

## Technology Stack
- Backend: Python/Java
- Frontend: React/Angular
- Database: PostgreSQL/MongoDB

## Components
1. User Interface Layer
2. Business Logic Layer
3. Data Access Layer

## Security
- Authentication & Authorization
- Data Encryption
- Secure Communications""",
                    "implementation": """# Implementation Strategy

## Phases
1. Initial Setup & Core Features
2. Integration & Testing
3. Deployment & Optimization

## Team Structure
- Frontend Developers
- Backend Developers
- DevOps Engineers
- QA Team""",
                    "rationale": """# Decision Rationale

## Why This Approach
- Matches project requirements
- Balances cost and performance
- Supports future scaling

## Risk Assessment
1. Technical Risks
2. Timeline Risks
3. Resource Risks

## Mitigation Strategies
- Detailed planning
- Regular reviews
- Continuous testing"""
                },
                "option2": {
                    "overview": """# Solution Overview

## Architecture Approach
- Cloud-native architecture
- Microservices-based design

## Key Benefits
1. High availability
2. Easy scaling
3. Modern architecture

## Main Features
- Distributed system
- Cloud services integration
- Advanced monitoring""",
                    "technical": """# Technical Details

## Technology Stack
- Cloud Platform: AWS/Azure
- Containerization: Docker/Kubernetes
- Serverless Components

## Components
1. Microservices
2. API Gateway
3. Message Queue
4. Data Store""",
                    "implementation": """# Implementation Strategy

## Phases
1. Cloud Infrastructure Setup
2. Service Implementation
3. Integration & Testing
4. Deployment

## Team Structure
- Cloud Architects
- DevOps Engineers
- Full-stack Developers
- SRE Team""",
                    "rationale": """# Decision Rationale

## Why This Approach
- Modern and future-proof
- Highly scalable
- Cost-effective long-term

## Risk Assessment
1. Complexity Risks
2. Integration Risks
3. Skills Gap Risks

## Mitigation Strategies
- Team training
- Phased implementation
- Expert consultation"""
                }
            }

    def _get_fallback_scope_questions(self) -> List[str]:
        return [
            "What are the specific business objectives this project needs to achieve?",
            "What are the main constraints in terms of timeline and budget?",
            "What are the critical technical limitations or requirements?",
            "Who are the key stakeholders and what are their expectations?",
            "What are the non-negotiable requirements for this project?",
            "What existing systems or processes need to be considered?"
        ]

    def _get_fallback_solution_questions(self) -> List[str]:
        return [
            "What architectural patterns have worked well in your organization?",
            "What are your scalability and performance requirements?",
            "What is your team's experience with different technology stacks?",
            "How do you prefer to handle deployment and operations?",
            "What are your primary security and compliance needs?",
            "What is your preferred development methodology?"
        ]

def initialize_session_state():
    """
    Initializes all required session state variables for the Streamlit app
    This ensures persistence of data between reruns and handles the multi-step form process
    """
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {}
    if 'scope_questions' not in st.session_state:
        st.session_state.scope_questions = []
    if 'scope_answers' not in st.session_state:
        st.session_state.scope_answers = {}
    if 'solution_questions' not in st.session_state:
        st.session_state.solution_questions = []
    if 'solution_answers' not in st.session_state:
        st.session_state.solution_answers = {}
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}

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
        steps = ["Project Description", "Scope Definition", "Solution Exploration", "Final Recommendations"]
        st.write("Current Step:", steps[st.session_state.current_step])
    
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
                with st.spinner("Generating scope questions..."):
                    st.session_state.scope_questions = agent.generate_scope_questions(
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
            
        st.write("### Scope Definition")
        with st.form("scope_questions_form"):
            answers = {}
            for i, question in enumerate(st.session_state.scope_questions):
                answer = st.text_input(
                    f"Q{i+1}: {question}",
                    key=f"scope_q_{i}",
                    help="Be as specific as possible"
                )
                if answer:
                    answers[question] = answer
            
            submit_answers = st.form_submit_button("Continue to Solution Exploration")
            
            if submit_answers:
                st.session_state.scope_answers = answers
                with st.spinner("Generating solution questions..."):
                    st.session_state.solution_questions = agent.generate_solution_questions(
                        st.session_state.project_info,
                        st.session_state.scope_answers
                    )
                st.session_state.current_step = 2
                st.rerun()
    
    # Step 3: Architecture Plan Display
    elif st.session_state.current_step == 2:
        # Add a back button
        if st.button("← Back to Scope Definition"):
            st.session_state.current_step = 1
            st.rerun()
            
        st.write("### Solution Exploration")
        with st.form("solution_questions_form"):
            answers = {}
            for i, question in enumerate(st.session_state.solution_questions):
                answer = st.text_input(
                    f"Q{i+1}: {question}",
                    key=f"solution_q_{i}",
                    help="Consider both technical and organizational aspects"
                )
                if answer:
                    answers[question] = answer
            
            submit_answers = st.form_submit_button("Generate Final Recommendations")
            
            if submit_answers:
                st.session_state.solution_answers = answers
                with st.spinner("Generating final recommendations..."):
                    st.session_state.recommendations = agent.generate_final_recommendations(
                        st.session_state.project_info,
                        st.session_state.scope_answers,
                        st.session_state.solution_answers
                    )
                st.session_state.current_step = 3
                st.rerun()
    
    # Step 4: Final Recommendations
    elif st.session_state.current_step == 3:
        # Add a back button
        if st.button("← Back to Solution Exploration"):
            st.session_state.current_step = 2
            st.rerun()
            
        st.write("### Final Recommendations")
        
        option_tab1, option_tab2 = st.tabs(["Option 1", "Option 2"])
        
        with option_tab1:
            overview_tab1, tech_tab1, impl_tab1, rationale_tab1 = st.tabs([
                "Solution Overview", "Technical Details", 
                "Implementation Strategy", "Rationale"
            ])
            with overview_tab1:
                st.markdown(st.session_state.recommendations['option1']['overview'])
            with tech_tab1:
                st.markdown(st.session_state.recommendations['option1']['technical'])
            with impl_tab1:
                st.markdown(st.session_state.recommendations['option1']['implementation'])
            with rationale_tab1:
                st.markdown(st.session_state.recommendations['option1']['rationale'])
        
        with option_tab2:
            overview_tab2, tech_tab2, impl_tab2, rationale_tab2 = st.tabs([
                "Solution Overview", "Technical Details", 
                "Implementation Strategy", "Rationale"
            ])
            with overview_tab2:
                st.markdown(st.session_state.recommendations['option2']['overview'])
            with tech_tab2:
                st.markdown(st.session_state.recommendations['option2']['technical'])
            with impl_tab2:
                st.markdown(st.session_state.recommendations['option2']['implementation'])
            with rationale_tab2:
                st.markdown(st.session_state.recommendations['option2']['rationale'])

if __name__ == "__main__":
    main() 