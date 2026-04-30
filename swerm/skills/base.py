from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSkill(ABC):
    """모든 에이전트 스킬의 기본 클래스"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """스킬의 고유 이름"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """스킬이 무엇을 하는지 에이전트에게 설명하는 문구"""
        pass

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """실제 로직 수행"""
        pass
