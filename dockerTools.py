import asyncio
import subprocess
from typing import Dict, Tuple

async def execute_command(command: str) -> Tuple[str, str]:
    """Execute a shell command asynchronously."""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Command failed with error: {stderr.decode()}")
    return stdout.decode(), stderr.decode()

async def pull_docker_container(docker_param: str) -> Dict[str, str]:
    """Pull a Docker container."""
    try:
        stdout, stderr = await execute_command(f"docker pull {docker_param}")
        return {"stdout": stdout, "stderr": stderr}
    except Exception as error:
        raise RuntimeError(f"exec error: {str(error)}")

async def run_docker_container(docker_param: str) -> str:
    """Run a Docker container."""
    try:
        command = f"docker run -d --rm -p 127.0.0.1:3000:3000 {docker_param}"
        print(f"command: {command}")
        stdout, stderr = await execute_command(command)
        # stdout contains the container ID
        return stdout.strip()
    except Exception as error:
        raise RuntimeError(f"exec error: {str(error)}")

async def reset_docker_container(docker_param: str) -> str:
    """Reset a Docker container."""
    try:
        # Get docker image from container ID
        stdout, _ = await execute_command(
            f'docker ps -f "id={docker_param}" --format "{{{{.Image}}}}"'
        )
        docker_container = stdout.strip()
        
        # Stop container
        await execute_command(f"docker stop {docker_param}")
        
        # Run new container
        new_id = await run_docker_container(docker_container)
        return new_id
    except Exception as error:
        raise RuntimeError(f"exec error: {str(error)}")

async def stop_docker_container(docker_param: str) -> Dict[str, str]:
    """Stop a Docker container."""
    try:
        stdout, stderr = await execute_command(f"docker stop {docker_param}")
        return {"stdout": stdout, "stderr": stderr}
    except Exception as error:
        raise RuntimeError(f"exec error: {str(error)}")

async def startAiCrawler(prompt):
    # in poetry shell
    try:
        stdout, stderr = await execute_command(f"python -m chromegpt -v -a auto-gpt -m gpt-4.0-turbo-preview -t \"{prompt}\" ")
        return {"stdout": stdout, "stderr": stderr}
    except Exception as error:
        raise RuntimeError(f"exec error: {str(error)}")
