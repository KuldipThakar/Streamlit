import streamlit as st
import pandas as pd
from config import PROJECT_DATA_DIR, PROJECT_FILES, TODAY
from data_utils import load_data, generate_task_alerts, get_project_summary
from visualizations import (
    create_progress_bar, create_status_pie_chart, create_overdue_bar_chart,
    create_task_histogram, create_task_timeline
 )
import os

# Set page configuration
st.set_page_config(page_title="BPL Dashboard", layout="wide")

# Load custom CSS
with open("styles/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def landing_page():
    """Render the landing page with project selection tiles."""
    st.title("📋 Project Dashboard")
    st.markdown("Select a project to view its task dashboard:")
    
    cols = st.columns(3)
    for idx, (project_name, _) in enumerate(PROJECT_FILES.items()):
        with cols[idx % 3]:
            if st.button(project_name, key=f"project_button_{project_name}"):
                st.session_state.selected_file = PROJECT_FILES[project_name]
                st.session_state.page = 'dashboard'
            st.markdown(f"<div class='project-tile'>{project_name}</div>", unsafe_allow_html=True)

def overview_page():
    """Render the project overview page with summary statistics and charts."""
    st.image("assets/bpl_logo.png", width=50)
    st.markdown("<h1 style='margin-top: -10px;'>Overall Project Status</h1>", unsafe_allow_html=True)
    
    if st.button("⬅ Back to Dashboard", key="back_to_dashboard"):
        st.session_state.page = 'dashboard'
        return

    if st.session_state.selected_file is None:
        st.error("No project selected. Please return to the project selection page.")
        if st.button("⬅ Back to Projects", key="back_to_projects"):
            st.session_state.page = 'landing'
        return

    project_name = [name for name, path in PROJECT_FILES.items() if path == st.session_state.selected_file][0]
    summary_df = get_project_summary(st.session_state.selected_file, project_name)
    
    if st.session_state.debug_mode:
        st.write("Debug: summary_df =", summary_df.to_dict())
        st.write("Debug: summary_df columns =", list(summary_df.columns))
        st.write("Debug: summary_df dtypes =", summary_df.dtypes.to_dict())
    
    if summary_df.empty:
        st.error("No project data available.")
        return

    st.subheader(f"📊 Summary for {project_name}")
    st.markdown(summary_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.subheader("📈 Project Progress")
    if 'Progress' in summary_df.columns:
        summary_df['Progress'] = summary_df['Progress'].astype(int)
    progress_fig, _ = create_progress_bar(summary_df, project_name)  # Unpack tuple, use only fig
    if st.session_state.debug_mode:
        st.write("Debug: Project progress figure data =", progress_fig.data)
    st.plotly_chart(progress_fig, use_container_width=True, key="overview_progress_chart")

    st.subheader("🧩 Status Distribution")
    st.plotly_chart(create_status_pie_chart(summary_df, project_name), use_container_width=True, key="overview_status_chart")

    st.subheader("🚨 Overdue Tasks")
    st.plotly_chart(create_overdue_bar_chart(summary_df, project_name), use_container_width=True, key="overview_overdue_chart")

    st.markdown('<div class="signature">Code by Kuldip</div>', unsafe_allow_html=True)

def dashboard_page():
    """Render the main dashboard page with task details and visualizations."""
    st.image("assets/bpl_logo.png", width=50)
    st.markdown("<h1 style='margin-top: -10px;'>Task Tracker Dashboard</h1>", unsafe_allow_html=True)
    
    # Debug mode toggle
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode, key="debug_mode_toggle")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅ Back to Projects", key="back_to_projects_dashboard"):
            st.session_state.page = 'landing'
            st.session_state.selected_file = None
            st.session_state.show_remarks = None
            return
    with col2:
        if st.button("Overall Project Status", key="to_overview "):
            st.session_state.page = 'overview'
            return

    if st.session_state.selected_file is None:
        st.info("No project file selected. Please return to the project selection page.")
        return

    df = load_data(st.session_state.selected_file)
    if df is None:
        st.error("Failed to load project data. Please check the file format and columns .")
        return

    st.subheader("🔍 Filter by Assignee")
    assignees = df['Assignees'].unique().tolist()
    selected_assignee = st.selectbox("Facet: Select Assignee", ["All"] + assignees, key="assignee_select")
    filtered_df = df if selected_assignee == "All" else df[df['Assignees'].str.contains(selected_assignee, case=False)]
    
    st.subheader("🚨 Task Alerts")
    alerts = generate_task_alerts(filtered_df, TODAY)
    if alerts and isinstance(alerts, list) and all(isinstance(a, dict) for a in alerts):
        try:
            alert_df = pd.DataFrame(alerts)
            def style_alerts(row):
                if row['Alert Type'] == 'critical':
                    return ['color: red; font-weight: bold; animation: blink 1s infinite'] * len(row)
                elif row['Alert Type'] == 'warning':
                    return ['color: orange; font-weight: bold'] * len(row)
                return [''] * len(row)
            st.markdown(alert_df.style.apply(style_alerts, axis=1).to_html(escape=False), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error creating alert DataFrame: {str(e)}")
    else:
        st.info("No alerts at this time.")
    
    st.subheader("📋 Task Data")
    display_df = filtered_df.copy()
    for idx, row in display_df.iterrows():
        end_date = row['End date']
        if pd.notnull(end_date) and end_date.date() < TODAY:
            display_df['Task No'] = display_df['Task No'].astype(str)
            display_df.at[idx, 'Task No'] = f"<span class='overdue-task'>{row['Task No']}</span>"
    st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.subheader("🎯 Select Task to check Progress")
    if filtered_df.empty:
        st.warning("No tasks available for the selected assignee.")
        task_options = ["All"]
    else:
        task_options = ["All"] + [f"Task No: {row['Task No']} - {row['Task']}" for _, row in filtered_df.iterrows()]
    selected_task_option = st.selectbox("Select Task No and Description", task_options, key="task_select")
    selected_task = None
    if selected_task_option != "All":
        try:
            task_number = int(selected_task_option.split(" - ")[0].replace("Task No: ", ""))
            selected_task = task_number
        except (IndexError, ValueError):
            st.error(f"Error parsing Task No from selection: {selected_task_option}.")

    # Progress bar section
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div style='padding-top: 84px;'></div>", unsafe_allow_html=True)
        st.subheader("📈 Task Progressbar")
        if st.session_state.debug_mode:
            st.write("Debug: Filtered DataFrame Shape =", filtered_df.shape)
            st.write("Debug: Selected Task =", selected_task)
    # Ensure Progress column is integer
        if 'Progress' in filtered_df.columns:
            filtered_df['Progress'] = filtered_df['Progress'].astype(int)
        progress_fig, remaining_days_text = create_progress_bar(filtered_df, selected_task=selected_task, today=TODAY)
        if st.session_state.debug_mode:
            st.write("Debug: Progress Figure Data =", progress_fig.data)
        if progress_fig.data:
            st.plotly_chart(progress_fig, use_container_width=True, key=f"progress_chart_{selected_task or 'default'}")
        else:
            st.warning("Progress bar could not be rendered due to invalid data.")
        st.write(f"**Deadline Status:** {remaining_days_text}")

    with col2:
        st.subheader("🧱 Task Progress Histogram")
        hist_types = [
            "Simple Bar (Progress by Task)",
            "Grouped Bar (Progress by Assignee)",
            "Stacked Bar (Count by Status)",
            "Progress Distribution (Binned)",
            "Per-Task Progress (One Bin per Task)"
        ]
        selected_hist_type = st.selectbox("Choose Histogram Style", hist_types, index=4, key="hist_select")
        hist_fig = create_task_histogram(filtered_df, selected_hist_type)
        st.plotly_chart(hist_fig, use_container_width=True, key=f"histogram_chart_{selected_hist_type}")

    # Timeline section
    st.subheader("🕒 Task Timeline")
    if st.session_state.debug_mode:
        st.write("Debug: Timeline Selected Task =", selected_task)
    timeline_fig, current_status = create_task_timeline(filtered_df, selected_task, TODAY)
    if st.session_state.debug_mode:
        st.write("Debug: Timeline Figure Data =", timeline_fig.data)
    col_overdue, col_button = st.columns([3, 1])
    with col_overdue:
        if selected_task is not None:
            task_data = filtered_df[filtered_df['Task No'] == selected_task]
            if not task_data.empty and pd.notnull(task_data['End date'].iloc[0]):
                end_date = pd.to_datetime(task_data['End date'].iloc[0]).date()
                if TODAY > end_date:
                    st.markdown(
                        "<span style='color:red; font-weight:bold; animation: blink 1s infinite;'>⚠️ This task is OVERDUE!</span>",
                        unsafe_allow_html=True
                    )
    with col_button:
        if selected_task is not None:
            if st.button("Explain", key=f"explain_timeline_{selected_task}"):
                st.session_state.show_remarks = selected_task
    if timeline_fig.data:
        st.plotly_chart(timeline_fig, use_container_width=True, key=f"timeline_chart_{selected_task or 'default'}")
    else:
        st.warning("Timeline could not be rendered due to invalid data.")
    st.write(f"**Current Status:** {current_status}")

    # Single remarks block after timeline
    if st.session_state.show_remarks is not None:
        task_data = filtered_df[filtered_df['Task No'] == st.session_state.show_remarks]
        if not task_data.empty:
            remarks = task_data['Remarks'].iloc[0]
            if pd.notnull(remarks):
                st.markdown(f"**Remarks for Task {st.session_state.show_remarks}:** {remarks}")
            else:
                st.info(f"No remarks available for Task No: {st.session_state.show_remarks}")
        else:
            st.warning(f"No data found for Task No: {st.session_state.show_remarks}")

    st.subheader("📊 Overall Project Status")
    pie_fig = create_status_pie_chart(filtered_df, project_name=None)
    st.plotly_chart(pie_fig, use_container_width=True, key="status_pie_chart")

    st.subheader("Task Summary")
    total_tasks = filtered_df.shape[0]
    completed = filtered_df[filtered_df['Status'].str.lower() == 'completed'].shape[0]
    in_progress = filtered_df[filtered_df['Status'].str.lower() == 'in progress'].shape[0]
    not_started = filtered_df[filtered_df['Status'].str.lower() == 'not started'].shape[0]
    st.write(f"**Total Tasks:** {total_tasks}")
    st.write(f"**Completed:** {completed}")
    st.write(f"**In Progress:** {in_progress}")
    st.write(f"**Not Started:** {not_started}")

    st.markdown('<div class="signature">Code by Kuldip</div>', unsafe_allow_html=True)

def main():
    """Main function to initialize session state and render the appropriate page."""
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None
    if 'show_remarks' not in st.session_state:
        st.session_state.show_remarks = None
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

    if st.session_state.page == 'landing':
        landing_page()
    elif st.session_state.page == 'overview':
        overview_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
