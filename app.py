import streamlit as st
import openai
from typing import List, Dict
import json

# Configure page and API key
st.set_page_config(page_title="Architect Guru", page_icon="🏗️", layout="wide")
openai.api_key = st.secrets["OPENAI_API_KEY"]

class ArchitectAgent:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        
    def _get_completion(self, messages: List[Dict]) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def generate_questions(self, project_description: str, challenges: List[str]) -> List[str]:
        prompt = f"""
        As an expert software architect, generate relevant questions to gather more information about this project:
        
        Project Description: {project_description}
        Main Challenges: {', '.join(challenges)}
        
        Generate 5-8 specific questions about:
        1. The industry and business context
        2. Technical requirements and constraints
        3. Team capabilities and resources
        4. Timeline and budget considerations
        5. Security and compliance needs (if applicable)
        
        Return the questions as a JSON array of strings.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert software architect."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._get_completion(messages)
        return json.loads(response)
    
    def generate_architecture_plan(self, project_info: Dict, answers: Dict) -> Dict:
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
            {"role": "system", "content": "You are an expert software architect."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        analysis = self._get_completion(messages)
        
        # Generate the architecture plan
        plan_prompt = f"""
        Based on this analysis:
        
        {analysis}
        
        Generate a comprehensive architecture plan with three different versions:
        1. Technical Overview: Detailed technical architecture including patterns, technologies, and implementation guidelines
        2. Management Summary: Focus on resources, timeline, risks, and key decisions for project managers and tech leads
        3. Executive Brief: High-level overview focusing on business value, costs, and strategic advantages
        
        Return the response as a JSON object with three keys: 'technical', 'management', and 'executive',
        each containing markdown-formatted content.
        """
        
        messages.append({"role": "assistant", "content": analysis})
        messages.append({"role": "user", "content": plan_prompt})
        
        response = self._get_completion(messages)
        return json.loads(response)

def initialize_session_state():
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {}
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'architecture_plan' not in st.session_state:
        st.session_state.architecture_plan = None

def main():
    st.title("🏗️ Architect Guru")
    st.subheader("Your AI Software Architecture Consultant")
    
    # Initialize the agent
    agent = ArchitectAgent()
    initialize_session_state()
    
    if st.session_state.current_step == 0:
        st.write("### Project Description")
        with st.form("project_info"):
            project_description = st.text_area(
                "Describe your software project:",
                placeholder="E.g., A mobile banking app with enhanced security features..."
            )
            challenges = st.multiselect(
                "Select your main challenges:",
                ["Security", "Time to Market", "Performance", "User Experience", "Scalability", "Cost Efficiency"]
            )
            submit_button = st.form_submit_button("Generate Questions")
            
            if submit_button and project_description:
                st.session_state.project_info = {
                    "description": project_description,
                    "challenges": challenges
                }
                with st.spinner("Generating questions..."):
                    st.session_state.questions = agent.generate_questions(
                        project_description, challenges
                    )
                st.session_state.current_step = 1
                st.rerun()
    
    elif st.session_state.current_step == 1:
        st.write("### Project Analysis Questions")
        with st.form("questions"):
            for i, question in enumerate(st.session_state.questions):
                answer = st.text_input(
                    f"Q{i+1}: {question}",
                    key=f"q_{i}",
                    help="Type 'don't know' if you're unsure about this aspect"
                )
                if answer:
                    st.session_state.answers[question] = answer
            
            submit_answers = st.form_submit_button("Generate Architecture Plan")
            
            if submit_answers:
                with st.spinner("Analyzing and generating architecture plan..."):
                    st.session_state.architecture_plan = agent.generate_architecture_plan(
                        st.session_state.project_info,
                        st.session_state.answers
                    )
                st.session_state.current_step = 2
                st.rerun()
    
    elif st.session_state.current_step == 2:
        st.write("### Architecture Recommendation")
        
        tab1, tab2, tab3 = st.tabs(["Technical Overview", "Management Summary", "Executive Brief"])
        
        with tab1:
            st.markdown(st.session_state.architecture_plan['technical'])
            
        with tab2:
            st.markdown(st.session_state.architecture_plan['management'])
            
        with tab3:
            st.markdown(st.session_state.architecture_plan['executive'])
        
        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main() 