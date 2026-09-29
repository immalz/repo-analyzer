from typing import Iterable


def belongs_to(name: str, packages: Iterable[str]) -> bool:
    """True si `name` es uno de los paquetes o esta dentro de ellos.

    Ejemplos: "java" cubre "java.util.List" pero NO "javax.persistence";
    "com.acme.cart" cubre "com.acme.cart.Cart" pero NO "com.acme.cartitem.Line".
    """
    return any(name == p or name.startswith(p + ".") for p in packages)
