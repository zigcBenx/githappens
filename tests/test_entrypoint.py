import importlib.util
import pathlib
import unittest


class EntrypointTest(unittest.TestCase):
    def test_entrypoint_exposes_main(self):
        path = pathlib.Path(__file__).resolve().parents[1] / "gitHappens.py"
        spec = importlib.util.spec_from_file_location("gitHappens", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
