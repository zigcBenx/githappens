from commands.deploy import find_production_deployment


def test_find_production_deployment_matches_mapping():
    pipelines = [{"id": 1, "status": "success"}]

    def jobs_loader(project_id, pipeline_id):
        return [{"name": "deploy-to-production", "stage": "deploy", "status": "success"}]

    result = find_production_deployment(
        pipelines,
        jobs_loader,
        project_id=123,
        production_mappings={"123": {"stage": "deploy", "job": "deploy-to-production"}},
    )

    assert result["pipeline"] == pipelines[0]
    assert result["production_job"]["name"] == "deploy-to-production"
