import argparse
import logging
from .jobs import DatabricksJobManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Databricks Job Deployer")
    parser.add_argument("--databricks-host", required=True)
    parser.add_argument("--databricks-token", required=True)
    parser.add_argument("--environment", required=True, choices=["production", "staging", "dev"])
    
    args = parser.parse_args()
    
    try:
        manager = DatabricksJobManager(
            host=args.databricks_host,
            token=args.databricks_token,
            environment=args.environment
        )
        
        manager.create_job("training.yml")
        manager.create_job("inference.yml")
        
    except Exception as e:
        logging.error(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()