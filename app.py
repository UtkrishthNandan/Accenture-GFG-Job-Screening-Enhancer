
from pdfloader_to_text import pdfloader_to_text
import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
llm=ChatGroq(
    temperature=0.05,
    groq_api_key=st.secrets["GROQ_API_KEY_VERSATILE"],
    model_name='llama-3.3-70b-versatile'
)
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    
    .title {
        text-align: center;
        margin-top: 0;
        padding-top: 0;
    }
    .st-emotion-cache-t1wise {
    margin-top: 0 !important;
        padding-top: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 class='title'>Job Screening Enhancer</h1>", unsafe_allow_html=True) 

col1, col2 = st.columns([4, 5])
job_desc_df=pd.read_csv('job_description.csv',index_col="Job Title")
if "job_desc_summary" not in st.session_state:
    st.session_state.job_desc_summary=""


with col1:
    job_option=st.selectbox(label='Select the job description',options=job_desc_df.index)
    job_prompt_extract=PromptTemplate.from_template(
            template="""
            #YOU ARE GIVEN THE FOLLOWING JOB DESCRIPTION:
            {job_desc}
            #Summarize it in 100 words.In one paragraph
            Output format: 
            Job Description(in bold):[summary in 150 words](in italics) 
            Required skills(in bold);[required skills in 100 words(keep it short)](in italics) 
            same format for experience, qualifications, and job responsibilities
            Do not leave blank new lines
            (NO PREAMBLE)
            """)
    job_chain_extract=job_prompt_extract | llm
    job_res=job_chain_extract.invoke(input={'job_desc':job_desc_df.loc[job_option]})
    st.markdown(f"{job_res.content}")

with col2:
    uploaded_files=st.file_uploader(label='pdf upload',type='pdf',accept_multiple_files=True)
    candidates_dict=dict()
    for uploaded_file in uploaded_files:
        
        if uploaded_file :
            temp_file_path = f"uploads/{uploaded_file.name}"
            with open(temp_file_path, "wb") as file:
                file.write(uploaded_file.getvalue())
        pdf_text=pdfloader_to_text(temp_file_path)
        #st.write(pdf_text)
        candidates_dict[uploaded_file.name[:-4]]={'pdf_text':str(pdf_text)}
    def clear_output():
        st.session_state.generated_score=""
        st.session_state.dataframe=None

    def generate_matching_scores():
        clear_output()
        for candidate_ID in candidates_dict.keys(): 
            prompt_extract=PromptTemplate.from_template(
            template="""
            You are an expert HR recruiter. Your task is to evaluate a candidate's resume against a provided job description and generate a numerical matching score reflecting the candidate's suitability.

                **Job Description:**
                {job_desc}

                **Candidate Resume:**
                {pdf_text}

                **Evaluation Criteria and Scoring Rubric:**
                ###DO NOT OUTPUT YOUR THINKING
                * **Skills (0-38 points):**
                    * 0: No matching skills.
                    * 1-10: Basic understanding of few matching skills.
                    * 11-20: Intermediate proficiency in some matching skills.
                    * 21-30: Advanced proficiency in most matching skills.
                    * 31-40: Expert proficiency in all required skills.
                * **Experience (0-32 points):**
                    * 0: No relevant experience.
                    * 1-10: Limited, tangential experience.
                    * 11-20: Relevant experience, but limited depth.
                    * 21-30: Extensive, directly relevant experience, with demonstrated impact. Consider the quality of experience, not just the years.
                * **Education (0-23 points):**
                    * 0: No relevant education.
                    * 1-10: Some relevant coursework or partial degree.
                    * 11-20: All required education or higher degree, with relevant specializations.
                * **Keyword Match (0-7 points):**
                    * 0: No relevant keywords matched.
                    * 1-5: Some relevant keywords matched.
                    * 6-10: Most or all relevant keywords matched, with natural language context.

                **Fit Factor (Consider in the Rationale):**

                * Assess the candidate's career trajectory and alignment with the job's responsibilities.
                * Consider any subtle indications of cultural fit or passion for the role, even if not explicitly stated.
                
                **Instructions:**    
                Carefully compare the candidate's resume to *each* requirement of the job description, paying close attention to nuances and subtle differences.
                
                ### OUTPUT the final calculated(dont show calculation) matching score (out of 1000( 1000 indicates perfect match,750 is the threshold for selection))and the email of the candidate based on the evaluation only.
                ###OUTPUT FORMAT:[matching score] [email] #Do not write "matching score" or "email"
                (NO PREAMBLE):

                    """
            )
            chain_extract=prompt_extract | llm
            res=chain_extract.invoke(input={'job_desc':job_desc_df.loc[job_option],'pdf_text':candidates_dict[candidate_ID]['pdf_text']})
            #st.session_state.generated_score+="Candidate ID:{candidate_ID}\t\t Matching Score:{res_content}\n" .format(candidate_ID=candidate_ID,res_content=res.content.split(" ")[0])
            
            
            candidates_dict[candidate_ID]['matching_score']=int(res.content.split(" ")[0])
            candidates_dict[candidate_ID]['email']=res.content.split(" ")[1]
        generate_table()
            

    def generate_table():
        candidate_ids=[]
        matching_scores=[]
        candidate_emails=[]
        for key in candidates_dict.keys():
            candidate_ids+=[str(key)]
            matching_scores+=[candidates_dict[key]['matching_score']]
            candidate_emails+=[candidates_dict[key]['email']]
        evaluated_candidate_dict={'Candidate_ID':candidate_ids,'Matching_Scores':matching_scores,'Candidate_Email':candidate_emails}
        temp_df=pd.DataFrame(data=evaluated_candidate_dict)
        #temp_df=temp_df.sort_values(by='Matching_Scores',ascending=False)
        
        #st.markdown(temp_df.style.hide(axis="index").to_html(), unsafe_allow_html=True)    
            
        st.session_state.dataframe=temp_df[temp_df['Matching_Scores']>750]

    st.button("Generate Matching Scores",on_click=generate_matching_scores)
    if "generated_score" not in st.session_state:
        st.session_state.generated_score=""
    st.text(st.session_state.generated_score)

    if "dataframe" not in st.session_state:
        st.session_state.dataframe=None
    if st.session_state.dataframe is not None:
        st.markdown(st.session_state.dataframe.style.hide(axis="index").to_html(), unsafe_allow_html=True)


