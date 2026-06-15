from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar


BT_SUCCESS = "success"
BT_FAILURE = "failure"
BT_RUNNING = "running"

# Behavior Tree универсальный, 
# но внутри одного дерева все узлы работают с одним и тем же типом контекста
TContext = TypeVar("TContext")


class BehaviorNode(Protocol[TContext]):
    # обновить
    def tick(self, context: TContext) -> str:
        ...


@dataclass
class ConditionNode:
    condition: Callable[[TContext], bool]

    def tick(self, context: TContext) -> str:
        if self.condition(context):
            return BT_SUCCESS
        return BT_FAILURE


@dataclass
class ActionNode:
    action: Callable[[TContext], str]

    def tick(self, context: TContext) -> str:
        return self.action(context)


# Sequence успешна только если все дети успешны
# это логическое И для статусов детей
@dataclass
class Sequence:
    children: list[BehaviorNode]

    def tick(self, context: TContext) -> str:
        for child in self.children:
            status = child.tick(context)
            if status != BT_SUCCESS:
                return status

        return BT_SUCCESS


# Selector успешна, если хотя бы один ребенок успешен
# это логическое ИЛИ для статусов детей
@dataclass
class Selector:
    children: list[BehaviorNode]

    def tick(self, context: TContext) -> str:
        for child in self.children:
            status = child.tick(context)
            if status != BT_FAILURE:
                return status

        return BT_FAILURE
