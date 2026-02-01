import subprocess
import os
import json
import logging
from typing import Optional
from langchain_core.tools import Tool

# Configure logger for this module
logger = logging.getLogger(__name__)

class TerraformTool:
    """A tool for running Terraform commands."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        logger.info(f"TerraformTool initialized with base_dir: {base_dir}")

    def _run_command(self, command: list[str], cwd: Optional[str] = None) -> str:
        """Run a shell command and return the output."""
        full_cwd = os.path.join(self.base_dir, cwd) if cwd else self.base_dir
        if not os.path.exists(full_cwd):
            logger.info(f"Creating directory: {full_cwd}")
            os.makedirs(full_cwd, exist_ok=True)

        logger.info(f"Running command: {' '.join(command)} in {full_cwd}")
        try:
            result = subprocess.run(
                command,
                cwd=full_cwd,
                capture_output=True,
                text=True,
                check=False
            )
            output = result.stdout
            if result.stderr:
                logger.warning(f"Command produced stderr: {result.stderr}")
                output += "\nErrors:\n" + result.stderr

            logger.debug(f"Command output: {result.stdout}")
            return output
        except Exception as e:
            logger.error(f"Exception occurred while running command: {str(e)}", exc_info=True)
            return f"Exception occurred: {str(e)}"

    def init(self, directory: str = ".") -> str:
        """Run terraform init."""
        logger.info(f"Initializing terraform in {directory}")
        return self._run_command(["terraform", "init"], cwd=directory)

    def plan(self, directory: str = ".") -> str:
        """Run terraform plan."""
        logger.info(f"Generating terraform plan in {directory}")
        return self._run_command(["terraform", "plan"], cwd=directory)

    def apply(self, directory: str = ".") -> str:
        """Run terraform apply -auto-approve."""
        logger.info(f"Applying terraform changes in {directory}")
        return self._run_command(["terraform", "apply", "-auto-approve"], cwd=directory)

    def destroy(self, directory: str = ".") -> str:
        """Run terraform destroy -auto-approve."""
        logger.info(f"Destroying terraform infrastructure in {directory}")
        return self._run_command(["terraform", "destroy", "-auto-approve"], cwd=directory)

    def output(self, directory: str = ".") -> str:
        """Run terraform output."""
        logger.info(f"Getting terraform output in {directory}")
        return self._run_command(["terraform", "output"], cwd=directory)

    def write_file(self, filename: str, content: str, directory: str = ".") -> str:
        """Write a file (e.g. main.tf) to the specified directory."""
        full_dir = os.path.join(self.base_dir, directory)
        if not os.path.exists(full_dir):
            logger.info(f"Creating directory for file: {full_dir}")
            os.makedirs(full_dir, exist_ok=True)

        filepath = os.path.join(full_dir, filename)
        logger.info(f"Writing file: {filepath}")
        try:
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"Successfully wrote {filename} to {directory}")
            return f"Successfully wrote {filename} to {directory}"
        except Exception as e:
            logger.error(f"Error writing file {filepath}: {str(e)}", exc_info=True)
            return f"Error writing file: {str(e)}"

def get_terraform_tools(base_dir: str = "terraform_data"):
    tf = TerraformTool(base_dir=base_dir)

    return [
        Tool(
            name="terraform_init",
            func=tf.init,
            description="Run terraform init in a directory. Useful to initialize a new terraform configuration."
        ),
        Tool(
            name="terraform_plan",
            func=tf.plan,
            description="Run terraform plan in a directory. Shows what changes will be made."
        ),
        Tool(
            name="terraform_apply",
            func=tf.apply,
            description="Run terraform apply in a directory. Deploys the infrastructure. Use with caution."
        ),
        Tool(
            name="terraform_destroy",
            func=tf.destroy,
            description="Run terraform destroy in a directory. Destroys the infrastructure."
        ),
        Tool(
            name="terraform_output",
            func=tf.output,
            description="Run terraform output in a directory. Shows the outputs of the deployment."
        ),
        Tool(
            name="write_terraform_file",
            func=lambda q: tf.write_file(**json.loads(q)) if q.strip().startswith("{") else "Error: input must be a JSON string like {\"filename\": \"main.tf\", \"content\": \"...\", \"directory\": \".\"}",
            description="Write a terraform file. Input should be a JSON string with keys: filename, content, directory (optional)."
        )
    ]
