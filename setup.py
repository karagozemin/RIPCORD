from setuptools import find_packages, setup

setup(
    name="ripcord",
    version="0.1.0",
    description="RIPCORD MVP - real-time liquidation rescue + risk execution firewall",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
)
