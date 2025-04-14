import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
from ..execution.engine import JobExecutionEngine
from ..storage.job_store import JobStore
from jobsonTwo.specs.loader import JobSpecLoader
import threading
import json
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize components
spec_loader = JobSpecLoader()
job_store = JobStore(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jobs'))
job_engine = JobExecutionEngine(job_store)

def get_job_types():
    """Get list of available job types from specs directory"""
    try:
        specs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specs')
        specs = []
        for spec_file in os.listdir(specs_dir):
            if spec_file.endswith('.yaml'):
                spec_path = os.path.join(specs_dir, spec_file)
                spec = spec_loader.load_from_file(spec_path)
                # Add the job type ID (filename without extension)
                spec['id'] = os.path.splitext(spec_file)[0]
                specs.append(spec)
        return specs
    except Exception as e:
        print(f"Error loading job types: {e}")
        return []

@app.route('/')
def index():
    """Home page showing recent jobs and stats"""
    jobs = job_store.list_jobs(limit=5)
    stats = {
        'total_jobs': len(job_store.list_jobs()),
        'running_jobs': len(job_store.list_jobs(status='running')),
        'completed_jobs': len(job_store.list_jobs(status='completed')),
        'failed_jobs': len(job_store.list_jobs(status='failed'))
    }
    job_types = get_job_types()
    
    # Add status colors for badges
    for job in jobs:
        status_colors = {
            'pending': 'warning',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger',
            'stopped': 'secondary'
        }
        job['status_color'] = status_colors.get(job['status'], 'secondary')
    
    return render_template('index.html', jobs=jobs, stats=stats, job_types=job_types)

@app.route('/jobs')
def jobs():
    """List all jobs"""
    jobs = job_store.list_jobs()
    
    # Add status colors for badges
    for job in jobs:
        status_colors = {
            'pending': 'warning',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger',
            'stopped': 'secondary'
        }
        job['status_color'] = status_colors.get(job['status'], 'secondary')
    
    return render_template('jobs.html', jobs=jobs)

@app.route('/jobs/new', methods=['GET', 'POST'])
def new_job():
    """Create and start a new job"""
    if request.method == 'GET':
        job_type = request.args.get('type')
        if not job_type:
            job_types = get_job_types()
            return render_template('new_job.html', job_types=job_types)
        
        try:
            specs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specs')
            spec_path = os.path.join(specs_dir, f"{job_type}.yaml")
            spec = spec_loader.load_from_file(spec_path)
            return render_template('new_job.html', spec=spec, job_type=job_type)
        except Exception as e:
            flash(f"Error loading job spec: {str(e)}", 'error')
            return redirect(url_for('new_job'))
    
    elif request.method == 'POST':
        job_type = request.args.get('type')
        if not job_type:
            flash("No job type specified", 'error')
            return redirect(url_for('new_job'))
        
        try:
            specs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'specs')
            spec_path = os.path.join(specs_dir, f"{job_type}.yaml")
            spec = spec_loader.load_from_file(spec_path)
            inputs = {}
            
            # Process form inputs
            for input_spec in spec['expectedInputs']:
                input_id = input_spec['id']
                if input_spec['type'] == 'file':
                    if input_id in request.files:
                        file = request.files[input_id]
                        if file.filename:
                            filename = secure_filename(file.filename)
                            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                            file.save(filepath)
                            inputs[input_id] = filepath
                else:
                    inputs[input_id] = request.form.get(input_id)
            
            # Create job
            job_id = job_store.create_job(
                spec=spec,
                inputs=inputs,
                name=request.form.get('name', f"{spec['name']} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
                description=request.form.get('description', '')
            )
            
            # Start job execution in background
            thread = threading.Thread(
                target=execute_job_background,
                args=(job_id, spec, inputs)
            )
            thread.daemon = True
            thread.start()
            
            return redirect(url_for('job_details', job_id=job_id))
        
        except Exception as e:
            flash(f"Error creating job: {str(e)}", 'error')
            return redirect(url_for('new_job'))

@app.route('/jobs/<job_id>')
def job_details(job_id):
    """Show details of a specific job"""
    job = job_store.get_job(job_id)
    if not job:
        flash("Job not found", 'error')
        return redirect(url_for('jobs'))
    
    # Add status color for badge
    status_colors = {
        'pending': 'warning',
        'running': 'info',
        'completed': 'success',
        'failed': 'danger',
        'stopped': 'secondary'
    }
    job['status_color'] = status_colors.get(job['status'], 'secondary')
    
    # Read output file contents if available
    if job.get('results') and job['results'].get('output_files'):
        job['results']['output_contents'] = {}
        for output_id, output_path in job['results']['output_files'].items():
            # Check if file is a binary file based on extension
            file_ext = os.path.splitext(output_path)[1].lower()
            binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.pdf', '.zip', '.exe', '.bin'}
            
            if file_ext in binary_extensions:
                job['results']['output_contents'][output_id] = "Binary file - available for download"
            else:
                try:
                    with open(output_path, 'r') as f:
                        job['results']['output_contents'][output_id] = f.read()
                except UnicodeDecodeError:
                    # If we can't decode the file as text, it's probably binary
                    job['results']['output_contents'][output_id] = "Binary file - available for download"
                except Exception as e:
                    print(f"Error reading output file {output_path}: {e}")
                    job['results']['output_contents'][output_id] = f"Error reading output file: {str(e)}"
    
    return render_template('job_details.html', job=job)

@app.route('/jobs/<job_id>/stop', methods=['POST'])
def stop_job(job_id):
    """Stop a running job"""
    try:
        job_engine.stop_job(job_id)
        flash("Job stopped successfully", 'success')
    except Exception as e:
        flash(f"Error stopping job: {str(e)}", 'error')
    return redirect(url_for('job_details', job_id=job_id))

@app.route('/jobs/<job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job"""
    try:
        job_engine.delete_job(job_id)
        flash("Job deleted successfully", 'success')
        return redirect(url_for('jobs'))
    except Exception as e:
        flash(f"Error deleting job: {str(e)}", 'error')
        return redirect(url_for('job_details', job_id=job_id))

@app.route('/jobs/<job_id>/output/<output_id>')
def download_output(job_id, output_id):
    """Download a job output file"""
    try:
        job = job_store.get_job(job_id)
        if not job or not job.get('results') or not job['results'].get('output_files'):
            flash("Output file not found", 'error')
            return redirect(url_for('job_details', job_id=job_id))
        
        output_files = job['results']['output_files']
        if output_id not in output_files:
            flash("Output file not found", 'error')
            return redirect(url_for('job_details', job_id=job_id))
        
        output_path = output_files[output_id]
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading output: {str(e)}", 'error')
        return redirect(url_for('job_details', job_id=job_id))

@app.route('/jobs/<job_id>/input/<input_id>')
def download_input(job_id, input_id):
    """Download a job input file"""
    try:
        job = job_store.get_job(job_id)
        if not job or not job.get('inputs'):
            flash("Input file not found", 'error')
            return redirect(url_for('job_details', job_id=job_id))
        
        if input_id not in job['inputs']:
            flash("Input file not found", 'error')
            return redirect(url_for('job_details', job_id=job_id))
        
        input_path = job['inputs'][input_id]
        return send_file(input_path, as_attachment=True)
    except Exception as e:
        flash(f"Error downloading input: {str(e)}", 'error')
        return redirect(url_for('job_details', job_id=job_id))

def execute_job_background(job_id: str, spec: dict, inputs: dict):
    """Execute a job in the background"""
    try:
        print(f"Starting background job execution for {job_id}")
        print(f"Job spec: {json.dumps(spec, indent=2)}")
        print(f"Job inputs: {json.dumps(inputs, indent=2)}")
        
        job_engine.execute_job(job_id, spec, inputs)
        print(f"Background job execution completed for {job_id}")
    except Exception as e:
        print(f"Error executing job {job_id}: {str(e)}")
        job_store.update_job_status(job_id, 'failed', {'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=3001) 