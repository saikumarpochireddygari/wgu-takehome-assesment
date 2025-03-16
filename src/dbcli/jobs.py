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
        return self.client.jobs.create(
            name=config.name,
            tasks=[
                jobs.Task(
                    task_key=config.name.lower().replace(" ", "_"),
                    notebook_task=jobs.NotebookTask(notebook_path=config.notebook_path),
                    new_cluster=jobs.NewCluster(**config.cluster),
                )
            ],
            schedule=jobs.CronSchedule(
                quartz_cron_expression=config.schedule, timezone_id="UTC"
            ),
            tags=config.tags,
        )
