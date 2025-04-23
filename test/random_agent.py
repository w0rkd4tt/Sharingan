import pytest
from src.core.identity.user_agent import UserAgentManager

@pytest.fixture
def ua_manager():
    return UserAgentManager()

def test_user_agent_init(ua_manager):
    assert ua_manager is not None

def test_get_random_user_agent(ua_manager):
    ua = ua_manager.get_random()
    assert ua is not None
    assert isinstance(ua, str)
    assert len(ua) > 0