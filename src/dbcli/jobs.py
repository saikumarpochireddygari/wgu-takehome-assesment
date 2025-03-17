from databricks.sdk import WorkspaceClient

# from databricks.sdk.service.jobs import JobSettings, Task, Schedule, NotebookTask
from databricks.sdk.service import jobs
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel


class JobConfig(BaseModel):
    name: str
    notebook_path: str
    schedule: str
    cluster: Dict[str, Any]
    tags: Dict[str, str]


class DatabricksJobManager:
    def __init__(self, host: str, token: str, environment: str):
        self.client = WorkspaceClient(host=host, token=token)
        self.environment = environment

    def _load_config(self, config_file: str) -> JobConfig:
        config_path = Path("config/jobs") / config_file
        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        replacements = {"{environment}": self.environment}

        for key in ["name", "notebook_path"]:
            if key in config_data:
                for k, v in replacements.items():
                    config_data[key] = config_data[key].replace(k, v)

        if "tags" in config_data:
            config_data["tags"]["environment"] = self.environment

        return JobConfig(**config_data)

    def create_job(self, config_file: str):
        config = self._load_config(config_file)
        cluster_config = config.cluster  # Use the entire dictionary from YAML

        # Create a cluster using the WorkspaceClient.
        # Adjust parameters as needed; here we use keys from the YAML.
        cluster_response = self.client.clusters.create(
            cluster_name=f"{config.name}-cluster-{self.environment}",
            spark_version=cluster_config.get("spark_version"),
            node_type_id=cluster_config.get("node_type_id"),
            num_workers=cluster_config.get("num_workers"),
            autoscale=cluster_config.get("autoscale"),
            autotermination_minutes=cluster_config.get("autotermination_minutes", 15),
        ).result()

        return self.client.jobs.create(
            name=config.name,
            tasks=[
                jobs.Task(
                    task_key=config.name.lower().replace(" ", "_"),
                    notebook_task=jobs.NotebookTask(
                        notebook_path=config.notebook_path,
                        source=jobs.Source("WORKSPACE"),
                    ),
                    # Use the existing_cluster_id parameter to specify an existing cluster
                    existing_cluster_id=cluster_response.cluster_id,
                )
            ],
            schedule=jobs.CronSchedule(
                quartz_cron_expression=config.schedule, timezone_id="UTC"
            ),
            tags=config.tags,
        )
