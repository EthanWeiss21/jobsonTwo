import os
import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path
from jobsonTwo.storage.job_store import JobStore

class JobExecutionEngine:
    """Handles job execution and process management."""
    
    def __init__(self, job_store: JobStore):
        """Initialize the job execution engine.
        
        Args:
            job_store: JobStore instance for job state management
        """
        self.job_store = job_store
        self.running_jobs: Dict[str, subprocess.Popen] = {}
    
    def execute_job(self, job_id: str, spec: Dict[str, Any], inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a job according to its specification.
        
        Args:
            job_id: Job identifier
            spec: Job specification
            inputs: Job input values
            
        Returns:
            Job results dictionary or None if execution failed
        """
        # Create job directory
        job_dir = os.path.join(self.job_store.jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Set up logging
        log_file = os.path.join(job_dir, 'job.log')
        def log(message):
            with open(log_file, 'a') as f:
                f.write(f"{message}\n")
            print(message)
        
        try:
            log(f"Starting job execution for {job_id}")
            self.job_store.update_job_status(job_id, 'running')
            
            # Create input files
            input_files = self._create_input_files(job_dir, spec, inputs)
            log(f"Created input files: {input_files}")
            
            # Prepare command
            cmd = self._prepare_command(spec, job_dir)
            log(f"Prepared command: {cmd}")
            
            # Execute command
            log(f"Executing command in directory: {job_dir}")
            process = subprocess.Popen(
                cmd,
                cwd=job_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=dict(os.environ, JOB_DIR=job_dir)
            )
            
            # Store process reference
            self.running_jobs[job_id] = process
            
            # Wait for completion
            stdout, stderr = process.communicate()
            log(f"Command execution completed with return code: {process.returncode}")
            log(f"stdout: {stdout}")
            log(f"stderr: {stderr}")
            
            # Process output files
            output_files = self._process_output_files(job_dir, spec)
            log(f"Processed output files: {output_files}")
            
            # Save results
            results = {
                'output_files': output_files,
                'stdout': stdout,
                'stderr': stderr,
                'return_code': process.returncode,
                'log_file': log_file
            }
            
            results_file = os.path.join(job_dir, 'results.json')
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            log(f"Saved results to {results_file}")
            
            # Update job status
            if process.returncode == 0:
                self.job_store.update_job_status(job_id, 'completed', results)
                log("Job completed successfully")
            else:
                self.job_store.update_job_status(job_id, 'failed', results)
                log("Job failed")
            
            return results
            
        except Exception as e:
            log(f"Error executing job: {e}")
            import traceback
            log(traceback.format_exc())
            self.job_store.update_job_status(job_id, 'failed', {'error': str(e)})
            return None
    
    def stop_job(self, job_id: str) -> bool:
        """Stop a running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was stopped, False otherwise
        """
        if job_id in self.running_jobs:
            process = self.running_jobs[job_id]
            process.terminate()
            process.wait()
            del self.running_jobs[job_id]
            self.job_store.update_job_status(job_id, 'stopped')
            return True
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job and stop it if running.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was deleted, False otherwise
        """
        # Stop job if running
        self.stop_job(job_id)
        
        # Delete job files
        return self.job_store.delete_job(job_id)
    
    def _create_input_files(self, job_dir: str, spec: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, str]:
        """Create input files for job execution."""
        input_files = {}
        
        for input_spec in spec['expectedInputs']:
            input_id = input_spec['id']
            input_value = inputs.get(input_id)
            
            if input_value is not None:
                input_file = os.path.join(job_dir, f'input_{input_id}.txt')
                
                if input_spec['type'] == 'file':
                    # Copy input file to job directory
                    import shutil
                    shutil.copy2(input_value, input_file)
                else:
                    # Write input value to file
                    with open(input_file, 'w') as f:
                        f.write(str(input_value))
                
                input_files[input_id] = input_file
        
        return input_files
    
    def _prepare_command(self, spec: Dict[str, Any], job_dir: str) -> list:
        """Prepare command for job execution."""
        cmd = [spec['execution']['application']]
        
        # Process arguments with string interpolation
        processed_args = []
        for arg in spec['execution']['arguments']:
            if isinstance(arg, str):
                # Replace all ${inputs.xyz} with the actual values
                processed_arg = arg
                while '${inputs.' in processed_arg:
                    start = processed_arg.find('${inputs.')
                    end = processed_arg.find('}', start) + 1
                    input_id = processed_arg[start + 9:end - 1]  # 9 is length of '${inputs.'
                    input_file = os.path.join(job_dir, f'input_{input_id}.txt')
                    if os.path.exists(input_file):
                        with open(input_file, 'r') as f:
                            value = f.read().strip()
                        processed_arg = processed_arg[:start] + value + processed_arg[end:]
                    else:
                        processed_arg = processed_arg[:start] + processed_arg[end:]
                processed_args.append(processed_arg)
            else:
                processed_args.append(arg)
        
        cmd.extend(processed_args)
        return cmd
    
    def _process_output_files(self, job_dir: str, spec: Dict[str, Any]) -> Dict[str, str]:
        """Process output files from job execution."""
        output_files = {}
        
        for output in spec['outputs']:
            output_id = output['id']
            output_path = os.path.join(job_dir, output['path'])
            
            if os.path.exists(output_path):
                output_files[output_id] = output_path
        
        return output_files 