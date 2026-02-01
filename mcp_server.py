from mcp.server.fastmcp import FastMCP
from terraform_tools import TerraformTool
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('.mcp-server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
logger.info("Initializing FastMCP server...")
mcp = FastMCP("Terraform-AWS-Agent")

# Initialize TerraformTool
# We'll use a dedicated directory for terraform files
DEPLOY_DIR = "terraform_data"
logger.info(f"Initializing TerraformTool with base_dir: {DEPLOY_DIR}")
tf = TerraformTool(base_dir=DEPLOY_DIR)

@mcp.tool()
def terraform_init(directory: str = ".") -> str:
    """Run terraform init in the specified directory."""
    logger.info(f"MCP Tool Called: terraform_init(directory='{directory}')")
    return tf.init(directory)

@mcp.tool()
def terraform_plan(directory: str = ".") -> str:
    """Run terraform plan in the specified directory."""
    logger.info(f"MCP Tool Called: terraform_plan(directory='{directory}')")
    return tf.plan(directory)

@mcp.tool()
def terraform_apply(directory: str = ".") -> str:
    """Run terraform apply in the specified directory. This deploys infrastructure."""
    logger.info(f"MCP Tool Called: terraform_apply(directory='{directory}')")
    return tf.apply(directory)

@mcp.tool()
def terraform_destroy(directory: str = ".") -> str:
    """Run terraform destroy in the specified directory. This removes infrastructure."""
    logger.info(f"MCP Tool Called: terraform_destroy(directory='{directory}')")
    return tf.destroy(directory)

@mcp.tool()
def terraform_output(directory: str = ".") -> str:
    """Get the terraform outputs for a deployment."""
    logger.info(f"MCP Tool Called: terraform_output(directory='{directory}')")
    return tf.output(directory)

@mcp.tool()
def write_terraform_file(filename: str, content: str, directory: str = ".") -> str:
    """Write a terraform (.tf) file to a directory."""
    logger.info(f"MCP Tool Called: write_terraform_file(filename='{filename}', directory='{directory}')")
    return tf.write_file(filename, content, directory)

if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run()
