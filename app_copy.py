import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Skill Mapping Analysis')

st.write("""
### Instructions
1. **Upload file for skill mapping**: This file should contain columns like 'Domain', 'Subdomain', 'First Name', 'Last Name', and 'Expertise Lvl'.
2. **Upload file for employee detailed information**: This file should contain detailed information about employees, including columns like 'EMP ID', 'First Name', 'Last Name', 'RM', 'Band', 'BU', 'DU Owner', and 'Working Location/City of Residence'.
""")

uploaded_file = st.file_uploader("Choose the Excel file for skill mapping", type="xlsx", key="skill_mapping")
uploaded_file_details = st.file_uploader("Choose the Excel file for employee detailed information", type="xlsx", key="employee_details")

if uploaded_file and uploaded_file_details:
    data_df = pd.read_excel(uploaded_file)
    details_df = pd.read_excel(uploaded_file_details)

    # Strip spaces from column names
    details_df.columns = details_df.columns.str.strip()
    
    # Debug: Print the columns of the details_df DataFrame
    print("Columns in employee details DataFrame after stripping spaces:")
    print(details_df.columns)
    
    filtered_data = data_df[data_df['Expertise Lvl'].isin(['Expert', 'Intermediate'])]

    summary_table = filtered_data.groupby(['Domain', 'Subdomain', 'Expertise Lvl'])['First Name'].nunique().unstack(fill_value=0)
    summary_table = summary_table.reset_index().set_index(['Domain', 'Subdomain'])

    def display_details(domain, subdomain, expertise_lvl):
        details = filtered_data[(filtered_data['Domain'] == domain) & 
                                (filtered_data['Subdomain'] == subdomain) & 
                                (filtered_data['Expertise Lvl'] == expertise_lvl)]
        
        st.write(f"### Details for {domain} - {subdomain} ({expertise_lvl})")
        
        # Merge with detailed information
        merged_details = pd.merge(details, details_df, on='First Name', how='left')
        merged_details.fillna('NA', inplace=True)
        
        # Debug: Print merged details after merge
        print("Merged Details after merge:")
        print(merged_details.head())
        
        # Ensure EMP ID is treated as an integer
        if 'EMP ID' in merged_details.columns:
            merged_details['EMP ID'] = pd.to_numeric(merged_details['EMP ID'], errors='coerce').fillna(0).astype(int)
        
        # Handle Last Name columns
        if 'Last Name_x' in merged_details.columns and 'Last Name_y' in merged_details.columns:
            merged_details['Last Name'] = merged_details['Last Name_x'].combine_first(merged_details['Last Name_y'])
            merged_details.drop(columns=['Last Name_x', 'Last Name_y'], inplace=True)
        
        # Debug: Print merged details after processing location
        print("Merged Details after processing location:")
        print(merged_details.head())

        # Define the order of display columns
        display_columns = ['EMP ID', 'First Name', 'Last Name', 'RM', 'Domain', 'Subdomain', 'Band', 'BU', 'DU Owner']
        display_columns = [col for col in display_columns if col in merged_details.columns]

        # Debug: Print final display columns
        print("Display Columns:")
        print(display_columns)

        st.table(merged_details[display_columns])

    selected_domain = st.selectbox('Select Domain:', summary_table.index.get_level_values('Domain').unique())

    st.write(f"## Summary Table for {selected_domain}")
    domain_data = summary_table.loc[selected_domain]
    st.table(domain_data)

    fig = px.bar(domain_data.reset_index(), x='Subdomain', y=['Expert', 'Intermediate'], barmode='group',
                 title=f'Number of Unique Experts and Intermediates by Subdomain in {selected_domain}')
    st.plotly_chart(fig)

    if st.checkbox('Show Subdomain Details'):
        selected_subdomain = st.selectbox('Select Subdomain:', domain_data.index.get_level_values('Subdomain').unique())
        selected_expertise_lvl = st.selectbox('Select Expertise Level:', ['Expert', 'Intermediate'])
        display_details(selected_domain, selected_subdomain, selected_expertise_lvl)
