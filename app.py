import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from datetime import datetime
import pytz

# Define the desired username and password
DESIRED_USERNAME = "admin"
DESIRED_PASSWORD = "y$9]0$ZWzfkh"

# Function to authenticate user
def authenticate(username, password):
    return username == DESIRED_USERNAME and password == DESIRED_PASSWORD

# Initialize session state to store data and update time
if 'employee_details_data' not in st.session_state:
    st.session_state.employee_details_data = []
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_modal' not in st.session_state:
    st.session_state.login_modal = False

# Function to show login modal
def show_login_modal():
    st.write("### Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login = st.button("Login", key="login_button_submit")  # Provide a unique key to the button
    if login:
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.experimental_rerun()  # Rerun the script to hide the login modal
        else:
            st.error("Invalid username or password!")

# Function to load and normalize CSV file
def load_and_normalize_csv(csv_file):
    if os.path.exists(csv_file):
        data = pd.read_csv(csv_file)
        data.columns = data.columns.str.strip().str.lower().str.replace(' ', '_')
        data = data.rename(columns={'first name': 'first_name', 'last name': 'last_name'})  # Renaming columns for consistency
        return data
    else:
        st.error(f"File {csv_file} not found.")
        return pd.DataFrame()

# Function to save dataframe to CSV
def save_to_csv(data, filename):
    data.to_csv(filename, index=False)
    st.success(f"Data saved to {filename}")

# Convert time to EST and format it
def format_time_to_est(time):
    est = pytz.timezone('US/Eastern')
    time_est = time.astimezone(est)
    return time_est.strftime('%Y-%m-%d %I:%M %p (EST)')

# Show login modal if not logged in
if not st.session_state.get("logged_in"):
    show_login_modal()
else:
    # Main menu
    st.sidebar.title("Navigation")
    main_menu = st.sidebar.radio("Main Menu", ["Home", "Basic Details", "Employee Details with Domain"])

    logout_clicked = st.sidebar.button("Logout", key="logout_button")
    if logout_clicked:
        st.session_state.logged_in = False
        st.experimental_rerun()

    if main_menu == "Home":
        st.title('Skill Mapping Analysis')

        # Display message if data was updated
        if st.session_state.last_update_time:
            formatted_time = format_time_to_est(st.session_state.last_update_time)
            st.info(f"Data was updated on {formatted_time}")

        st.write("### Select Domain")

        csv_file = 'final_transformed_data.csv'
        details_df = load_and_normalize_csv(csv_file)

        if 'domain' in details_df.columns:
            unique_domains = details_df['domain'].unique()
            selected_domain = st.selectbox("Domain", unique_domains)
            
            if selected_domain:
                filtered_df = details_df[details_df['domain'] == selected_domain]

                if 'subdomain' in filtered_df.columns and 'expertise' in filtered_df.columns:
                    # Filter for Expert and Intermediate levels only
                    filtered_expertise_df = filtered_df[filtered_df['expertise'].isin(['Expert', 'Intermediate'])]
                    
                    # Group and count the expertise levels per subdomain
                    expertise_counts = filtered_expertise_df.groupby(['subdomain', 'expertise']).size().unstack(fill_value=0).reset_index()

                    # Ensure the DataFrame has columns for both 'Expert' and 'Intermediate'
                    expertise_counts = expertise_counts.reindex(columns=['subdomain', 'Expert', 'Intermediate'], fill_value=0)
                    expertise_counts.columns = ['Subdomain', 'Expert', 'Intermediate']

                    # Add column-wise total
                    total_experts = expertise_counts['Expert'].sum()
                    total_intermediates = expertise_counts['Intermediate'].sum()
                    total_row = pd.DataFrame([['Total', total_experts, total_intermediates]], columns=['Subdomain', 'Expert', 'Intermediate'])
                    expertise_counts = pd.concat([expertise_counts, total_row], ignore_index=True)

                    # Summary Table
                    st.write("### Summary Table")
                    st.table(expertise_counts)

                    # Bar Chart
                    st.write("### Bar Chart")
                    fig = px.bar(
                        expertise_counts[expertise_counts['Subdomain'] != 'Total'],  # Exclude the Total row from the bar chart
                        x='Subdomain',
                        y=['Expert', 'Intermediate'],
                        title=f'Number of Experts and Intermediates in {selected_domain}',
                        labels={'value': 'Count', 'variable': 'Expertise Level'},
                        barmode='group'
                    )
                    st.plotly_chart(fig)

                    # Detailed View with Subdomains
                    st.write("### Detailed View with Subdomains")
                    if 'Subdomain' in expertise_counts.columns:
                        for i, row in expertise_counts.iterrows():
                            if row['Subdomain'] != 'Total':
                                subdomain = row['Subdomain']
                                experts = row['Expert']
                                intermediates = row['Intermediate']
                                total = experts + intermediates
                                with st.expander(f"{subdomain} ({total} Total: {experts} Experts, {intermediates} Intermediates)"):
                                    subdomain_table = filtered_df[(filtered_df['subdomain'] == subdomain) & (filtered_df['expertise'].isin(['Expert', 'Intermediate']))]
                                    st.write(f"#### Subdomain: {subdomain}")
                                    st.dataframe(subdomain_table)
                    else:
                        st.error("The 'subdomain' column is not present in the summary data.")
                else:
                    st.error("The required columns 'subdomain' and 'expertise' are not present in the filtered data.")
        else:
            st.error("The required 'domain' column is not present in the data.")

    elif main_menu == "Basic Details":
        st.title("Basic Details")

        csv_file = 'final_transformed_data.csv'
        data = pd.read_csv(csv_file)
        data.columns = data.columns.str.strip().str.lower().str.replace(' ', '_')
        data = data.rename(columns={'first name': 'first_name', 'last name': 'last_name'})

        # Exclude domain, subdomain, and expertise columns and get unique employee details
        columns_to_exclude = ['domain', 'subdomain', 'expertise']
        subset_columns = [col for col in ['first_name', 'last_name', 'rm', 'project', 'bu', 'years_of_experience'] if col in data.columns]
        basic_details = data.drop(columns=columns_to_exclude, errors='ignore').drop_duplicates(subset=subset_columns)

        st.write("### Basic Employee Details")
        st.dataframe(basic_details)

        if st.button("Generate Unique Employee Details CSV"):
            download_link = generate_unique_employee_csv()
            if download_link:
                st.markdown(download_link, unsafe_allow_html=True)

    elif main_menu == "Employee Details with Domain":
        st.title("Employee Details with Domain")

        csv_file = 'final_transformed_data.csv'
        data = pd.read_csv(csv_file)
        data.columns = data.columns.str.strip().str.lower().str.replace(' ', '_')
        data = data.rename(columns={'first name': 'first_name', 'last name': 'last_name'})
        data = data.iloc[::-1]  # Reverse the DataFrame to show the most recent records first

        st.write("### Employee Details with Domain")

        # Upload new data functionality
        uploaded_file = st.file_uploader("Upload a CSV file to update the data", type=["csv"])
        if uploaded_file is not None:
            new_data = pd.read_csv(uploaded_file)
            new_data.columns = new_data.columns.str.strip().str.lower().str.replace(' ', '_')
            new_data = new_data.rename(columns={'first name': 'first_name', 'last name': 'last_name'})
            
            # Update the existing data with the new data
            st.session_state.employee_details_data = new_data.to_dict(orient='records')
            save_to_csv(new_data, csv_file)
            
            # Store the update time
            st.session_state.last_update_time = datetime.now()

        # Display the dataframe
        data = pd.DataFrame(st.session_state.employee_details_data)
        st.dataframe(data)

        # Download CSV button
        csv_string = data.to_csv(index=False)
        b64 = base64.b64encode(csv_string.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="employee_details.csv">Download CSV File</a>'
        st.markdown(href, unsafe_allow_html=True)
