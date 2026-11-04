"""UseCase, Scenario, Orchestrator (AT-90): один публичный метод `__call__`, зависимости строго по слоям.

- UseCase - одно действие на портах домена (репозитории, шлюзы, часы); другие UseCase не зовёт.
- Scenario - собирает UseCase'ы; репозитории и шлюзы можно, другие сценарии не зовёт.
- Orchestrator - управляет сценариями; репозитории и шлюзы можно, другие оркестраторы не зовёт.

Общий кусок нескольких UseCase - метод репозитория, отдельный UseCase или чистая функция в domain/util.
Классы ищутся в domain/usecase, domain/scenario, domain/orchestrator по суффиксу имени (UseCase, Scenario,
Orchestrator); зависимости - по аннотациям параметров конструктора.
Старые нарушения - _LEGACY_*: это храповик, исправил файл - убери его из списка.
"""
import ast
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_FEATURE_DIR = _ROOT / "bot" / "feature"
_ROLE_SUFFIXES = {
    "usecase": "UseCase",
    "scenario": "Scenario",
    "orchestrator": "Orchestrator",
}
# Суффиксы типов в конструкторе, которые роли запрещены
_FORBIDDEN_DEPENDENCIES = {
    "usecase": (
        "UseCase",
        "Scenario",
        "Orchestrator",
    ),
    "scenario": (
        "Scenario",
        "Orchestrator",
    ),
    "orchestrator": ("Orchestrator",),
}

# Только сокращать: публичные методы, кроме __call__, или нет __call__
_LEGACY_API = frozenset(
    {
        "admin/domain/scenario/GetRemindInfoTextScenario.py",
        "business/domain/scenario/GenerateAiReponseScenario.py",
        "business/domain/usecase/ApplyChatEventUseCase.py",
        "business/domain/usecase/DecideChatTransitionUseCase.py",
        "business/domain/usecase/GenerateAndSendStepUseCase.py",
        "business/domain/usecase/GetChatStrListUseCase.py",
        "business/domain/usecase/GetForwardOriginTextForAiUseCase.py",
        "business/domain/usecase/GetInactiveChatListUseCase.py",
        "business/domain/usecase/GetSystemInstructionUseCase.py",
        "business/domain/usecase/GetUserListUseCase.py",
        "business/domain/usecase/HandleAiResponseUseCase.py",
        "business/domain/usecase/HandleChatStepUseCase.py",
        "business/domain/usecase/IsChatStepActualUseCase.py",
        "business/domain/usecase/ProcessChatEventUseCase.py",
        "business/domain/usecase/ReadMessageStepUseCase.py",
        "business/domain/usecase/SaveMessageUseCase.py",
        "business/domain/usecase/ScheduleChatStepUseCase.py",
        "business/domain/usecase/SendAiRequestUseCase.py",
        "business/domain/usecase/SendAnswerMessageUseCase.py",
        "business/domain/usecase/StartTypingStepUseCase.py",
        "business/domain/usecase/TypingLoopUseCase.py",
        "business/domain/usecase/UpdateUserTableFromChatHistoryUseCase.py",
    },
)
# Только сокращать: зависимость против слоя
_LEGACY_DEPENDENCIES = frozenset(
    {
        "business/domain/usecase/ApplyChatEventUseCase.py",
        "business/domain/usecase/GenerateAndSendStepUseCase.py",
        "business/domain/usecase/HandleChatStepUseCase.py",
        "business/domain/usecase/ProcessChatEventUseCase.py",
        "business/domain/usecase/ReadMessageStepUseCase.py",
        "business/domain/usecase/SendAiRequestUseCase.py",
        "business/domain/usecase/SendAnswerMessageUseCase.py",
        "business/domain/usecase/StartTypingStepUseCase.py",
    },
)


def test_when_reading_domain_classes_expect_only_call_public() -> None:
    # Arrange
    expected = _LEGACY_API

    # Act
    actual = frozenset(
        relative
        for relative, role_class in _role_classes()
        if _public_methods(role_class = role_class) != {"__call__"}
    )

    # Assert
    assert actual == expected, (
        "У UseCase, Scenario и Orchestrator один публичный метод - __call__, остальное приватное; "
        "два действия - два класса. Исправил старый файл - убери его из _LEGACY_API"
    )


def test_when_reading_constructors_expect_dependencies_by_layer() -> None:
    # Arrange
    expected = _LEGACY_DEPENDENCIES

    # Act
    actual = frozenset(
        relative
        for relative, role_class in _role_classes()
        if _forbidden_dependencies(
            role = Path(relative).parent.name,
            role_class = role_class,
        )
    )

    # Assert
    assert actual == expected, (
        "UseCase - только порты домена, Scenario - порты и UseCase'ы, Orchestrator - порты, UseCase'ы и сценарии; "
        "общий кусок - метод репозитория, отдельный UseCase или чистая функция в domain/util. "
        "Исправил старый файл - убери его из _LEGACY_DEPENDENCIES"
    )


def _role_classes() -> list[tuple[str, ast.ClassDef]]:
    classes: list[tuple[str, ast.ClassDef]] = []
    for role, suffix in _ROLE_SUFFIXES.items():
        for path in sorted(_FEATURE_DIR.glob(f"*/domain/{role}/*.py")):
            if path.name == "__init__.py":
                continue
            tree = ast.parse(path.read_text(encoding = "utf-8"))
            classes.extend(
                (path.relative_to(_FEATURE_DIR).as_posix(), node)
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name.endswith(suffix)
            )
    return classes


def _public_methods(role_class: ast.ClassDef) -> set[str]:
    return {
        node.name
        for node in role_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (not node.name.startswith("_") or node.name == "__call__")
    }


def _forbidden_dependencies(
    role: str,
    role_class: ast.ClassDef,
) -> list[str]:
    constructor = next(
        (
            node
            for node in role_class.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        ),
        None,
    )
    if constructor is None:
        return []
    annotations = [
        ast.unparse(argument.annotation)
        for argument in constructor.args.args[1:]
        if argument.annotation is not None
    ]
    return [
        annotation
        for annotation in annotations
        if annotation.endswith(_FORBIDDEN_DEPENDENCIES[role])
    ]
