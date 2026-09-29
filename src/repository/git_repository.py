import os
import shutil
import stat
import subprocess


class RepositoryCloneError(Exception):
    """El repositorio no se pudo clonar (rama inexistente, repo privado o URL invalida)."""


def clone_repository(url: str, branch: str, target_path: str) -> str:
    """Clona la rama indicada en `target_path` (borrando un clon previo) y devuelve el commit SHA."""
    if os.path.exists(target_path):
        shutil.rmtree(target_path, onerror=_remove_readonly)

    try:
        # core.longpaths evita checkouts incompletos en Windows (rutas > 260 caracteres).
        subprocess.run(["git", "-c", "core.longpaths=true", "clone", "--branch", branch, "--depth", "1", url, target_path],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        raise RepositoryCloneError(error.stderr.strip() or "git clone failed") from error

    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target_path, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _remove_readonly(func, path, _):
    # Git marca algunos archivos como solo lectura; en Windows hay que desbloquearlos para borrarlos.
    os.chmod(path, stat.S_IWRITE)
    func(path)
