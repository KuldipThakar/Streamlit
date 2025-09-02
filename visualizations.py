import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import plotly.graph_objs as go

def create_progress_bar(df, project_name=None, selected_task=None, today=None):
    """Create a progress bar for project or task."""

    if project_name is not None:
        required_columns = ['Project', 'Average Progress (%)']
        # Debug input data
        if 'debug_mode' in st.session_state and st.session_state.debug_mode:
            st.write(f"Debug: create_progress_bar input df (project_name={project_name}) =", df.to_dict())
        
        # Validate input
        if (df.empty or 
            not all(col in df.columns for col in required_columns) or 
            not pd.api.types.is_numeric_dtype(df['Average Progress (%)']) or 
            df['Average Progress (%)'].isna().all()):
            st.warning(f"No valid data for project progress chart of {project_name}. Ensure summary data contains valid 'Project' and numeric 'Average Progress (%)'.")
            fig = go.Figure()
            fig.update_layout(
                title=f"No Data for {project_name}",
                xaxis_title="Project",
                yaxis_title="Average Progress (%)",
                yaxis_range=[0, 100],
                annotations=[{
                    'text': 'No valid data to display',
                    'xref': 'paper',
                    'yref': 'paper',
                    'showarrow': False,
                    'font': {'size': 16}
                }]
            )
            if 'debug_mode' in st.session_state and st.session_state.debug_mode:
                st.write("Debug: Returning fallback figure due to invalid data")
            return fig, "No data"
        
        # Ensure Average Progress (%) is integer
        df = df.copy()  # Avoid modifying original DataFrame
        df['Average Progress (%)'] = pd.to_numeric(df['Average Progress (%)'], errors='coerce').fillna(0).clip(0, 100).astype(int)
        
        # Create figure
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Project'],
            y=df['Average Progress (%)'],
            text=df['Average Progress (%)'],
            textposition='auto',
            texttemplate='%{text:.0f}%',  # Display as integer with % symbol
            marker_color='skyblue',
            name='Average Progress'
        ))
        fig.update_layout(
            title=f"Average Progress for {project_name}",
            xaxis_title="Project",
            yaxis_title="Average Progress (%)",
            yaxis_range=[0, 100],
            yaxis=dict(tickformat='.0f'),  # Integer ticks on y-axis
            bargap=0.2
        )
        
        if 'debug_mode' in st.session_state and st.session_state.debug_mode:
            st.write("Debug: Project progress figure data =", fig.data)
        return fig, "N/A"
    
    if selected_task is not None:
        task_data = df[df['Task No'] == selected_task]
        if task_data.empty:
            st.warning(f"No data found for Task No: {selected_task}")
            return go.Figure(), "No task selected"
        # Convert progress to integer
        completion_rate = int(float(task_data['Progress'].iloc[0])) if pd.notnull(task_data['Progress'].iloc[0]) else 0
        task_description = task_data['Task'].iloc[0] if pd.notnull(task_data['Task'].iloc[0]) else "Unknown"
        start_date = task_data['Start date'].iloc[0]
        end_date = task_data['End date'].iloc[0]
        start_date_str = start_date.strftime('%Y-%m-%d') if pd.notnull(start_date) else "N/A"
        end_date_str = end_date.strftime('%Y-%m-%d') if pd.notnull(end_date) else "N/A"
        remaining_days = (end_date.date() - today).days if pd.notnull(end_date) and today else None
        remaining_days_text = f"Overdue by {-remaining_days} days" if remaining_days and remaining_days < 0 else f"{remaining_days} days remaining" if remaining_days else "No end date"
        title = (f"<b>Progress for Task No: {selected_task} ({task_data['Status'].iloc[0]})</b><br>"
                 f"<span style='font-size:1.0em;color:gray'>Description: {task_description}</span><br>"
                 f"<span style='font-size:1.0em;color:white'>Start: {start_date_str} | End: {end_date_str}</span>")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=completion_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 16}},
            number={'valueformat': '.0f'},  # Display as integer
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "black", 'tickformat': '.0f'},
                'bar': {'color': "darkblue", 'thickness': 0.2},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 75], 'color': "yellow"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        return fig, remaining_days_text
    
    completed_tasks = df[df['Status'].str.lower() == 'completed'].shape[0]
    total_tasks = df.shape[0]
    # Convert completion rate to integer
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    title = "Overall Task Completion Rate (%)<br><span style='font-size:0.8em;color:gray'>No specific task selected</span>"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=completion_rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        number={'valueformat': '.0f'},  # Display as integer
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "black", 'tickformat': '.0f'},
            'bar': {'color': "darkblue", 'thickness': 0.2},
            'steps': [
                {'range': [0, 50], 'color': "red"},
                {'range': [50, 75], 'color': "yellow"},
                {'range': [75, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    return fig, "No task selected"

def create_status_pie_chart(df, project_name=None):
    """Create a pie chart for status distribution."""
    if df.empty:
        st.warning("No data available for status distribution.")
        return go.Figure()
    if project_name is not None:
        status_counts = {
            'Completed': df['Completed'].sum(),
            'In Progress': df['In Progress'].sum(),
            'Not Started': df['Not Started'].sum()
        }
    else:
        status_counts = df['Status'].value_counts().to_dict()
    
    fig = go.Figure(data=[go.Pie(
        labels=list(status_counts.keys()),
        values=list(status_counts.values()),
        hole=0.4,
        textinfo='label+percent',
        marker=dict(colors=['green', 'orange', 'gray', 'red', 'blue', 'purple'])
    )])
    fig.update_layout(
        title="Project Status Distribution" if project_name is None else f"Status Distribution for {project_name}",
        showlegend=True
    )
    return fig

def create_overdue_bar_chart(df, project_name):
    """Create a bar chart for overdue tasks."""
    if df.empty:
        st.warning("No data available for overdue tasks.")
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Project'],
        y=df['Overdue Tasks'],
        text=df['Overdue Tasks'],
        textposition='auto',
        marker_color='red',
        name='Overdue Tasks'
    ))
    fig.update_layout(
        title=f"Overdue Tasks for {project_name}",
        xaxis_title="Project",
        yaxis_title="Number of Overdue Tasks",
        bargap=0.2
    )
    return fig

def create_task_histogram(df, hist_type):
    """Create a histogram based on the selected style."""
    if df.empty:
        st.warning("No data available for histogram.")
        return go.Figure()
    if hist_type == "Simple Bar (Progress by Task)":
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Task No'],
            y=df['Progress'],
            text=df['Progress'],
            textposition='auto',
            marker_color='skyblue',
            name='Progress'
        ))
        fig.update_layout(
            title="Progress by Task Number",
            xaxis_title="Task Number",
            yaxis_title="Progress (%)",
            bargap=0.2,
            yaxis_range=[0, 100]
        )
    elif hist_type == "Grouped Bar (Progress by Assignee)":
        fig = go.Figure()
        for assignee in df['Assignees'].unique():
            assignee_df = df[df['Assignees'].str.contains(assignee, case=False)]
            fig.add_trace(go.Bar(
                x=assignee_df['Task No'],
                y=assignee_df['Progress'],
                name=assignee,
                text=assignee_df['Progress'],
                textposition='auto'
            ))
        fig.update_layout(
            title="Progress by Task and Assignee",
            xaxis_title="Task Number",
            yaxis_title="Progress (%)",
            bargap=0.2,
            barmode='group',
            yaxis_range=[0, 100]
        )
    elif hist_type == "Stacked Bar (Count by Status)":
        fig = go.Figure()
        for status in df['Status'].unique():
            status_df = df[df['Status'] == status]
            fig.add_trace(go.Bar(
                x=status_df['Task No'],
                y=[1] * len(status_df),
                name=status,
                text=status,
                textposition='none'
            ))
        fig.update_layout(
            title="Task Count by Status and Task Number",
            xaxis_title="Task Number",
            yaxis_title="Number of Tasks",
            bargap=0.2,
            barmode='stack'
        )
    elif hist_type == "Progress Distribution (Binned)":
        fig = px.histogram(
            df,
            x='Progress',
            nbins=10,
            title="Distribution of Progress Values",
            labels={'Progress': 'Progress (%)'},
            histnorm='percent',
            color_discrete_sequence=['lightgreen']
        )
        fig.update_layout(
            xaxis_title="Progress (%)",
            yaxis_title="Percentage of Tasks",
            bargap=0.2
        )
    else:  # Per-Task Progress (One Bin per Task)
        def get_color(progress):
            if progress == 100:
                return "#187896"
            elif progress >= 75:
                return "#51C951"
            elif progress >= 50:
                return "#C5C560"
            elif progress >= 25:
                return "#B88323"
            else:
                return '#FF0000'
        
        colors = df['Progress'].apply(get_color).tolist()
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Task No'],
            y=df['Progress'],
            text=df['Progress'],
            textposition='auto',
            marker_color=colors,
            name='Progress',
            hovertemplate='Task: %{customdata}<br>Progress: %{y}%',
            customdata=df['Task']
        ))
        fig.update_layout(
            title="Progress Percentage per Task",
            xaxis_title="Task Number",
            yaxis_title="Progress (%)",
            yaxis_range=[0, 100],
            bargap=0.2,
            xaxis=dict(tickmode='linear', dtick=1),
            showlegend=False
        )
    return fig

def create_task_timeline(df, selected_task, today):
    """Create a timeline chart for a selected task."""
    if selected_task is None:
        st.warning("No task selected for timeline.")
        return go.Figure(), "No task selected"
    
    task_data = df[df['Task No'] == selected_task]
    if task_data.empty:
        st.warning(f"No data found for Task No: {selected_task}")
        return go.Figure(), "No task selected"
    
    start_date_raw = task_data['Start date'].iloc[0]
    end_date_raw = task_data['End date'].iloc[0]
    if pd.notnull(start_date_raw) and pd.notnull(end_date_raw):
        try:
            start_date = pd.to_datetime(start_date_raw).date()
            end_date = pd.to_datetime(end_date_raw).date()
        except Exception as e:
            st.warning(f"Invalid date format for Task No: {selected_task}: {str(e)}")
            return go.Figure(), "Invalid date"
    else:
        st.warning(f"Missing start or end date for Task No: {selected_task}")
        return go.Figure(), "Invalid date"
    
    if end_date < start_date:
        st.warning(f"Invalid duration for Task No: {selected_task} (end date before start date)")
        return go.Figure(), "Invalid duration"
    
    current_status = task_data['Status'].iloc[0] if pd.notnull(task_data['Status'].iloc[0]) else "Unknown"
    task_description = task_data['Task'].iloc[0] if pd.notnull(task_data['Task'].iloc[0]) else "Unknown"
    progress = float(task_data['Progress'].iloc[0]) if pd.notnull(task_data['Progress'].iloc[0]) else 0.0
    total_duration = (end_date - start_date).days
    elapsed_duration = (today - start_date).days
    overdue = today > end_date
    color = "red" if overdue else "lightgreen" if elapsed_duration / total_duration < 0.33 else "orange" if elapsed_duration / total_duration < 0.66 else "red"
    
    dates = [start_date, today, end_date]
    labels = ['Start', 'Today', 'End']
    progress_vals = [0, progress, 100]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=progress_vals,
        mode='lines+markers+text',
        text=labels,
        textposition='top center',
        marker=dict(size=10),
        line=dict(color=color, width=3),
        name=f"Task No: {selected_task}"
    ))
    fig.update_layout(
        title=f"Timeline for Task No: {selected_task} - {task_description}",
        xaxis_title="Date",
        yaxis_title="Progress (%)",
        yaxis_range=[0, 100],
        showlegend=False
    )
    return fig, current_status