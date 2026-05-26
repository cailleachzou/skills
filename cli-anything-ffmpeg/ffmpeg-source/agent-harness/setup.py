"""PyPI package configuration for cli-anything-ffmpeg."""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-ffmpeg",
    version="0.1.0",
    description="AI-friendly CLI harness for FFmpeg — transcode, probe, batch process",
    long_description=open("README.md", encoding="utf-8").read() if __import__('os').path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="DUDU&Cailleach",
    python_requires=">=3.8",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-ffmpeg=cli_anything.ffmpeg.ffmpeg_cli:cli",
        ],
    },
    package_data={
        "cli_anything.ffmpeg": ["tests/*"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v2.1 (LGPLv2.1)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video :: Conversion",
    ],
)