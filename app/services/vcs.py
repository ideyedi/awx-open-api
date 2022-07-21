import tempfile
from typing import List
from pathlib import Path
from git import Repo

INFRACM_AUTHOR_INFO = "InfraCM TF <wmporg_infra-cm@wemakeprice.com>"

# 절대경로로 남겨놔야 함
# 컨테이너 환경에서는 git push 할때에 cwd 가 /tmp/xxx 으로 변경되기 때문임
GIT_SSH_COMMAND = (
    f"ssh -i {Path('./app/keys/ci_infracm').resolve()} -o StrictHostKeyChecking=no"
)


class Vcs:
    """
    Version Control System Interface
    """

    def clone(self, repo: str, branch: str) -> Path:
        """
        $ git clone git@bitbucket.wemakeprice.com/...
        Args:
            repo (str): remote repo url
            branch (str): branch name

        Returns:
            Path: cloned repo path
        """
        pass

    def add(self, repo: Repo):
        pass

    def commit(self, repo: Repo, message: str, author: str):
        pass

    def merge(self, repo: Repo, branch: str, into: str):
        pass

    def push(self, repo: Repo, remote: str, branch: str):
        pass

    def checkoutBranch(self, repo: Repo, branch: str):
        pass


class Git(Vcs):
    """
    GitPython wrapper
    https://gitpython.readthedocs.io/
    """

    def clone(self, url: str, branch: str = "master") -> Repo:
        """
        Bitbucket 의 git 저장소인 `url` 을 tmp 디렉토리에 clone 합니다.
        """
        dirpath = tempfile.mkdtemp()
        repo = Repo.clone_from(
            url,
            dirpath,
            branch=branch,
            env={"GIT_SSH_COMMAND": GIT_SSH_COMMAND},
        )
        return repo

    def add(self, repo: Repo):
        repo.git.add(all=True)

    def commit(self, repo: Repo, message: str, author: str):
        repo.git.commit(
            "-m",
            message,
            author=author,
        )

    def merge(self, repo: Repo, branch: str, into: str, author: str):
        """
        merge `branch` into `into`
        `branch` -> `into`

        Args:
            repo (Repo): [description]
            branch (str): source branch
            into (str): target branch
        """
        with repo.git.custom_environment(GIT_SSH_COMMAND=GIT_SSH_COMMAND):
            repo.git.checkout(into)

            if author:
                repo.git.merge(branch, no_ff=True, no_commit=True)
                # $ git commit --author "author" --no-edit
                repo.git.commit("--no-edit", author=author)
            else:
                repo.git.merge(branch, no_ff=True)

            repo.git.checkout(branch)  # restore

    def push(self, repo: Repo, remote: str, branch: str):
        with repo.git.custom_environment(GIT_SSH_COMMAND=GIT_SSH_COMMAND):
            repo.git.push(remote, branch)

    def checkoutBranch(self, repo: Repo, branch: str):
        repo.git.checkout("-b", branch)
