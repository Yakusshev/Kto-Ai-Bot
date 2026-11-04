"""Единая структура фич (AT-90): эталонное дерево описано в скилле aiogram-bot-architecture.

feature/<имя>/ - только domain/, data/, entry/, di/ и public.py;
domain/ - только подпапки по роли, файлов в корне нет; у каждого пакета есть __init__.py.
entry/ - presenter/ (общий для клиентов), bot/ (Telegram), api/ (мини-аппа); файлов в корне нет.
Старые фичи с плоским entry/ и файлами в корне domain/ - в _LEGACY_*: это храповик, только сокращать.
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_DIR = _ROOT / "bot"
_FEATURE_DIR = _SOURCE_DIR / "feature"
_FEATURE_ENTRIES = frozenset(
    {
        "__init__.py",
        "public.py",
        "di",
        "domain",
        "data",
        "entry",
    },
)
_DOMAIN_ENTRIES = frozenset(
    {
        "__init__.py",
        "analytics",
        "const",
        "error",
        "gateway",
        "model",
        "orchestrator",
        "repository",
        "scenario",
        "state",
        "usecase",
        "util",
    },
)
_ENTRY_ENTRIES = frozenset(
    {
        "__init__.py",
        "api",
        "bot",
        "presenter",
    },
)
# Фичи с плоским entry/ до эталона. Только сокращать: переделал фичу по эталону - убери её
_LEGACY_FLAT_ENTRY = frozenset(
    {
        "admin",
        "business",
    },
)
# Файлы в корне domain/ до эталона. Только сокращать: перенёс файл в пакет роли - убери его
_LEGACY_DOMAIN_ROOT = frozenset(
    {
        "bot/feature/admin/domain/CommandConst.py",
        "bot/feature/admin/domain/FormatUserChatModelListUseCase.py",
        "bot/feature/admin/domain/GetAdminBotTokenUseCase.py",
        "bot/feature/admin/domain/HandleStopCommandUseCase.py",
        "bot/feature/business/domain/get_bot_token.py",
    },
)
# Файлы в repository/ с неверным именем. Только сокращать
_LEGACY_REPOSITORY_NAMES = frozenset(
    {
        "bot/feature/business/data/repository/DeepseekRepository.py",
        "bot/feature/business/domain/repository/DelayedTaskQueue.py",
    },
)


def test_when_listing_feature_root_expect_only_layers() -> None:
    # Arrange
    features = sorted(path for path in _FEATURE_DIR.iterdir() if path.is_dir() and path.name != "__pycache__")

    # Act
    actual = {
        _relative(feature): sorted(_entries(feature) - _FEATURE_ENTRIES)
        for feature in features
        if _entries(feature) - _FEATURE_ENTRIES
    }

    # Assert
    expected: dict[str, list[str]] = {}
    assert actual == expected, "В корне фичи - только domain/, data/, entry/, di/ и public.py"


def test_when_listing_domain_root_expect_only_role_packages() -> None:
    # Arrange
    domains = sorted(_FEATURE_DIR.glob("*/domain"))

    # Act
    actual = sorted(
        _relative(domain / name)
        for domain in domains
        for name in _entries(domain) - _DOMAIN_ENTRIES
        if _relative(domain / name) not in _LEGACY_DOMAIN_ROOT
    )

    # Assert
    expected: list[str] = []
    assert actual == expected, (
        "В корне domain/ - только подпапки: model, repository, gateway, analytics, const, state, error, usecase, "
        "scenario, orchestrator, util"
    )


def test_when_legacy_domain_root_fixed_expect_removed_from_list() -> None:
    # Arrange
    expected: list[str] = []

    # Act
    actual = sorted(path for path in _LEGACY_DOMAIN_ROOT if not (_ROOT / path).exists())

    # Assert
    assert actual == expected, "Файл перенесён или удалён - убери его из _LEGACY_DOMAIN_ROOT"


def test_when_package_has_modules_expect_init_file() -> None:
    # Arrange
    packages = {
        path.parent
        for top in (_SOURCE_DIR / "core", _FEATURE_DIR)
        for path in top.rglob("*.py")
        if "__pycache__" not in path.parts
    }

    # Act
    actual = sorted(_relative(package) for package in packages if not (package / "__init__.py").is_file())

    # Assert
    expected: list[str] = []
    assert actual == expected, "Добавь __init__.py: пакеты без него - неявные namespace-пакеты"


def test_when_listing_repository_packages_expect_repository_names() -> None:
    # Arrange
    violations = _repository_name_violations()

    # Act
    actual = sorted(violations - _LEGACY_REPOSITORY_NAMES)

    # Assert
    expected: list[str] = []
    assert actual == expected, (
        "В domain/repository - порты <Сущность>Repository, в data/repository - <Сущность>RepositoryImpl; "
        "порт, который не хранит данные (уведомить, отрисовать, поставить в очередь), - в domain/gateway"
    )


def test_when_legacy_repository_names_fixed_expect_removed_from_list() -> None:
    # Arrange
    violations = _repository_name_violations()

    # Act
    actual = sorted(_LEGACY_REPOSITORY_NAMES - violations)

    # Assert
    expected: list[str] = []
    assert actual == expected, "Файл переименован, перенесён или удалён - убери его из _LEGACY_REPOSITORY_NAMES"


def test_when_listing_entry_root_expect_only_client_packages() -> None:
    # Arrange
    entries = sorted(
        entry
        for entry in _FEATURE_DIR.glob("*/entry")
        if entry.parent.name not in _LEGACY_FLAT_ENTRY
    )

    # Act
    actual = {
        _relative(entry): sorted(_entries(entry) - _ENTRY_ENTRIES)
        for entry in entries
        if _entries(entry) - _ENTRY_ENTRIES
    }

    # Assert
    expected: dict[str, list[str]] = {}
    assert actual == expected, (
        "В корне entry/ - только presenter/ (Presenter и UiState), bot/ (хендлеры, экраны, клавиатуры) "
        "и api/ (мини-аппа)"
    )


def test_when_listing_legacy_flat_entries_expect_only_existing_flat_features() -> None:
    # Arrange
    expected: list[str] = []

    # Act
    actual = sorted(
        feature
        for feature in _LEGACY_FLAT_ENTRY
        if not (_FEATURE_DIR / feature / "entry").is_dir()
        or not _entries(_FEATURE_DIR / feature / "entry") - _ENTRY_ENTRIES
    )

    # Assert
    assert actual == expected, "Фича уже по эталону или без entry/ - убери её из _LEGACY_FLAT_ENTRY"


def _entries(directory: Path) -> set[str]:
    return {path.name for path in directory.iterdir() if path.name != "__pycache__"}


def _repository_name_violations() -> frozenset[str]:
    suffixes = {
        "domain/repository": "Repository.py",
        "data/repository": "RepositoryImpl.py",
    }
    return frozenset(
        _relative(path)
        for package, suffix in suffixes.items()
        for path in _FEATURE_DIR.glob(f"*/{package}/*.py")
        if path.name != "__init__.py" and not path.name.endswith(suffix)
    )


def _relative(path: Path) -> str:
    return path.relative_to(_ROOT).as_posix()
