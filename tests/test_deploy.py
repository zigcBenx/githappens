import unittest
from unittest import mock

from githappens.commands import deploy


class DeployCommandTest(unittest.TestCase):
    def test_last_production_deploy_uses_project_mapping(self):
        pipeline_response = mock.Mock(
            status_code=200,
            json=mock.Mock(
                return_value=[
                    {
                        "id": 77,
                        "status": "success",
                        "ref": "master",
                        "sha": "abcdef123456",
                        "web_url": "https://gitlab.example/pipelines/77",
                    }
                ]
            ),
        )
        jobs_response = mock.Mock(
            status_code=200,
            json=mock.Mock(
                return_value=[
                    {
                        "name": "production",
                        "stage": "deploy",
                        "status": "success",
                        "started_at": "2026-05-12T10:00:00Z",
                        "finished_at": "2026-05-12T10:02:00Z",
                        "duration": 120,
                    }
                ]
            ),
        )

        with mock.patch("githappens.commands.deploy.get_project_id", return_value=11), \
             mock.patch(
                 "githappens.commands.deploy.templates.get_production_mappings",
                 return_value={"11": {"stage": "deploy", "job": "production"}},
             ), \
             mock.patch("githappens.commands.deploy.requests.get", side_effect=[pipeline_response, jobs_response]) as get, \
             mock.patch("builtins.print") as print_mock:
            deploy.get_last_production_deploy()

        self.assertEqual(get.call_args_list[0].args[0], f"{deploy.config.API_URL}/projects/11/pipelines")
        self.assertEqual(get.call_args_list[1].args[0], f"{deploy.config.API_URL}/projects/11/pipelines/77/jobs")
        printed = "\n".join(str(call.args[0]) for call in print_mock.call_args_list)
        self.assertIn("Last Production Deployment", printed)
        self.assertIn("Job: production (success)", printed)


if __name__ == "__main__":
    unittest.main()
