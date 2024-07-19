import os
import sys
from . import ConfigGenerator

def generate_configs(lab_name):
    if (
        not os.environ.get("LAB_USERNAME", None)
        or not os.environ.get("LAB_PASSWORD", None)
    ):
        print("Lab config generation requires that both LAB_USERNAME and LAB_PASSWORD are set in the environment")
        exit(1)
    lab_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", lab_name))
    if not os.path.exists(lab_dir):
        print(f"Could not find a lab named {lab_name}")
        exit(2)

    generator = ConfigGenerator(lab_dir, os.environ["LAB_USERNAME"], os.environ["LAB_PASSWORD"])
    generator.build_configs()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: network_labs <command>")
        exit(-1)

    if sys.argv[1] == "generate_configs":
        if len(sys.argv) < 3:
            print("Usage: network_labs generate_configs <lab name>")
            exit(-2)
        generate_configs(sys.argv[2])
    else:
        print("Unknown command", sys.argv[1])
        exit(-3)
