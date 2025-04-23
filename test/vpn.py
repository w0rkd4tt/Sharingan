from src.core.vpn.nordvpn import NordVPNRotator


@pytest.fixture
def vpn():
    return NordVPNRotator()

def test_vpn_init(vpn):
    assert vpn is not None
    assert isinstance(vpn.vietnam_servers, list)
    assert isinstance(vpn.countries, list)
    assert vpn.vietnam_only == False

def test_set_vietnam_only(vpn):
    vpn.set_vietnam_only(True)
    assert vpn.vietnam_only == True

def test_connect_vpn(vpn):
    result = vpn.connect_vpn('us')
    assert isinstance(result, bool)

def test_get_current_ip(vpn):
    ip = vpn.get_current_ip()
    assert ip is not None
    assert isinstance(ip, str)