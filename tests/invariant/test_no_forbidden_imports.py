import ast
from pathlib import Path


SOURCE_ROOTS = (Path("apps"), Path("core"), Path("storage"), Path("scripts"))
NETWORK_OR_EXCHANGE_MODULES = {
    "aiohttp",
    "binance",
    "ccxt",
    "eth_account",
    "httpx",
    "hyperliquid",
    "requests",
    "socket",
    "websocket",
    "websockets",
}
PRODUCT_MODULE_PREFIXES = ("apps.", "core.", "storage.")


def _python_files() -> tuple[Path, ...]:
    return tuple(path for root in SOURCE_ROOTS if root.exists() for path in root.rglob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    return imports


def test_no_network_or_exchange_client_imports_are_introduced() -> None:
    offenders: list[tuple[Path, str]] = []

    for path in _python_files():
        for module in _imported_modules(path):
            root_module = module.split(".", maxsplit=1)[0]
            if root_module in NETWORK_OR_EXCHANGE_MODULES:
                offenders.append((path, module))

    assert offenders == []


def test_execution_imports_do_not_leak_into_upstream_modules() -> None:
    offenders: list[tuple[Path, str]] = []

    for path in _python_files():
        if path.parts[:2] == ("core", "execution"):
            continue
        for module in _imported_modules(path):
            if module == "core.execution" or module.startswith("core.execution."):
                offenders.append((path, module))

    assert offenders == []


def test_live_runner_imports_do_not_leak_into_offline_paths() -> None:
    offenders: list[tuple[Path, str]] = []

    for path in _python_files():
        if path.parts[:2] == ("apps", "live_runner"):
            continue
        for module in _imported_modules(path):
            if module == "apps.live_runner" or module.startswith("apps.live_runner."):
                offenders.append((path, module))

    assert offenders == []


def test_repository_validators_do_not_import_product_modules() -> None:
    offenders: list[tuple[Path, str]] = []

    for path in Path("scripts").rglob("*.py"):
        for module in _imported_modules(path):
            if module.startswith(PRODUCT_MODULE_PREFIXES):
                offenders.append((path, module))

    assert offenders == []
