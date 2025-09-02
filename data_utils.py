import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import threading
import os
from config import TODAY

# Thread-safe cache for loaded data
_data_cache = {}
_cache_lock = threading.Lock()

@st.cache_data
def load_data(file_path):
    """Load and process CSV or Excel data with caching."""
    with _cache_lock:
        if file_path in _data_cache:
            return _data_cache[file_path]

    try:
        if not os.path.exists(file_path):
            st.error(f"File not found: {file_path}")
            return None
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, delimiter=',', quotechar='"', on_bad_lines='warn')
        else:
            df = pd.read_excel(file_path)
        
        required_columns = ['Task No', 'Task', 'Status', 'Progress', 'Start date', 'End date', 'Assignees', 'Remarks']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing required columns in {file_path}: {', '.join(missing_columns)}")
            return None
        
        df = df[required_columns]
        df['Progress'] = pd.to_numeric(df['Progress'], errors='coerce').fillna(0)
        df['Start date'] = pd.to_datetime(df['Start date'], errors='coerce')
        df['End date'] = pd.to_datetime(df['End date'], errors='coerce')
        df['Task No'] = pd.to_numeric(df['Task No'], errors='coerce')
        
        if df['Task No'].isnull().any() or df['Task'].isnull().any() or df['Status'].isnull().any():
            st.error(f"Invalid or missing data in 'Task No', 'Task', or 'Status' columns in {file_path}")
            return None

        with _cache_lock:
            _data_cache[file_path] = df
        return df
    except Exception as e:
        st.error(f"Error loading file {file_path}: {str(e)}")
        return None

def generate_task_alerts(df, today):
    """Generate task alerts based on progress and deadlines."""
    alerts = []
    if df.empty:
        return alerts
    for _, row in df.iterrows():
        task_no = row['Task No']
        task_name = row['Task']
        progress = int(row['Progress']) if pd.notnull(row['Progress']) else 0.0
        start_date = row['Start date']
        end_date = row['End date']

        if pd.isnull(start_date) or pd.isnull(end_date):
            continue

        try:
            start_date = pd.to_datetime(start_date).date()
            end_date = pd.to_datetime(end_date).date()
        except Exception:
            continue

        if today < start_date or (end_date - start_date).days <= 0:
            continue

        duration = (end_date - start_date).days
        elapsed_days = (today - start_date).days
        timeline_percentage = min(elapsed_days / duration, 1.0) * 100

        alert_message = None
        alert_type = "normal"

        if today > end_date and progress < 100:
            alert_message = f"Task is overdue."
            alert_type = "critical"
        elif progress == 0 and elapsed_days >= 0:
            alert_message = f"Task has not been started."
            alert_type = "warning"
        elif timeline_percentage >= 75 and progress <= 60:
            alert_message = f"Task is critically behind; completion at risk."
            alert_type = "critical"
        elif timeline_percentage >= 50 and progress <= 30:
            alert_message = f"Task is running behind schedule."
            alert_type = "warning"
        elif timeline_percentage >= 25 and progress <= 15:
            alert_message = f"Task is at risk of delay."
            alert_type = "warning"

        if alert_message:
            alerts.append({
                'Task No': task_no,
                'Task': task_name,
                'Progress (%)': progress,
                'Alert': alert_message,
                'Alert Type': alert_type
            })
    return alerts

def get_project_summary(file_path, project_name):
    """Generate project summary statistics."""
    df = load_data(file_path)
    if df is None or df.empty:
        st.warning(f"No data loaded for project {project_name}. Check file path: {file_path}")
        return pd.DataFrame({
            'Project': [project_name],
            'Total Tasks': [0],
            'Completed': [0],
            'In Progress': [0],
            'Not Started': [0],
            'Average Progress (%)': [0.0],
            'Overdue Tasks': [0]
        })
    
    # Ensure Progress is numeric, convert non-numeric to 0
    df['Progress'] = pd.to_numeric(df['Progress'], errors='coerce').fillna(0)
    
    summary = {
        'Project': [project_name],
        'Total Tasks': [df.shape[0]],
        'Completed': [df[df['Status'].str.lower() == 'completed'].shape[0]],
        'In Progress': [df[df['Status'].str.lower() == 'in progress'].shape[0]],
        'Not Started': [df[df['Status'].str.lower() == 'not started'].shape[0]],
        'Average Progress (%)': [df['Progress'].mean() if not df['Progress'].empty else 0.0],
        'Overdue Tasks': [df[df['End date'].apply(lambda x: pd.to_datetime(x).date() < TODAY if pd.notnull(x) else False)].shape[0]]
    }
    return pd.DataFrame(summary)