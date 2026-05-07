import docker


class DockerService:
    def __init__(self):
        self.client = docker.from_env()

    def list_containers(self):
        return self.client.containers.list(all=True)

    def get_container(self, name):
        return self.client.containers.get(name)

    def start(self, name):
        self.get_container(name).start()

    def stop(self, name):
        self.get_container(name).stop()

    def restart(self, name):
        self.get_container(name).restart()

    def delete(self, name):
        self.get_container(name).remove(force=True)

    def logs(self, name, tail=200):
        return self.get_container(name).logs(tail=tail).decode("utf-8", errors="replace")

    def stats(self, name):
        return self.get_container(name).stats(stream=False)